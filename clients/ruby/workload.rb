# ActiveRecord (Rails 8) + pg workload, connection settings at their defaults
# (pool 5, checkout_timeout 5 s, prepared_statements true, Rails' built-in
# reconnect/retry for idempotent reads).
#
# Env: DATABASE_URL, CLIENT, RUN_TAG, RATE, DURATION_S, TIMEOUT_MS, OUT.
# Requests run on threads, as in a threaded app server. The 2 s deadline is
# the caller's: a reaper writes a timeout line at the deadline, and a late
# outcome is written as op "late_<op>".
require "active_record"
require "json"
require "time"

ActiveRecord::Base.establish_connection(ENV.fetch("DATABASE_URL"))
class Ledger < ActiveRecord::Base
  self.table_name = "ledger"
end

client = ENV.fetch("CLIENT")
tag = "#{client}/#{ENV['RUN_TAG']}"
rate = Integer(ENV.fetch("RATE", "50"))
dur = Float(ENV.fetch("DURATION_S", "90"))
timeout = Integer(ENV.fetch("TIMEOUT_MS", "2000")) / 1000.0

db = ActiveRecord::Base.connection_db_config.configuration_hash
warn "activerecord #{ActiveRecord::VERSION::STRING} pg #{PG::VERSION} pool=#{ActiveRecord::Base.connection_pool.size} " \
     "checkout_timeout=#{ActiveRecord::Base.connection_pool.checkout_timeout} prepared_statements=#{db.fetch(:prepared_statements, 'default(true)')}"

out = File.open(ENV.fetch("OUT"), "w")
mu = Mutex.new
outstanding = {}

write = ->(r) { mu.synchronize { out.puts(JSON.generate(r)) } }

classify = lambda do |e|
  cause = e.respond_to?(:cause) && e.cause ? e.cause : e
  state = cause.respond_to?(:result) && cause.result ? cause.result.error_field(PG::Result::PG_DIAG_SQLSTATE) : nil
  state ? "pg_#{state}" : e.class.name
end

stop = false
reaper = Thread.new do
  loop do
    now = Time.now.to_f
    expired = mu.synchronize do
      ks = outstanding.select { |_, (_, dl)| dl <= now }.keys
      ks.map { |k| outstanding.delete(k)[0] }
    end
    expired.each do |b|
      write.call(b.merge(ok: false, latency_ms: ((now - b[:ts_ms] / 1000.0) * 1000).round(3),
                         error_class: "timeout", error_message_verbatim: "client deadline #{(timeout * 1000).to_i}ms exceeded"))
    end
    break if stop && mu.synchronize { outstanding.empty? }
    sleep 0.05
  end
end

workers = Queue.new
running = []
200.times do
  running << Thread.new do
    while (job = workers.pop)
      i, base = job
      err = nil
      begin
        if base[:op] == "insert"
          Ledger.create!(client: tag, seq: base[:seq], ts: Time.now)
        else
          Ledger.maximum(:id)
        end
      rescue StandardError => e
        err = e
      end
      lat = ((Time.now.to_f - base[:ts_ms] / 1000.0) * 1000).round(3)
      mine = mu.synchronize { !outstanding.delete(i).nil? }
      rec = base.merge(ok: err.nil?, latency_ms: lat, error_class: err ? classify.call(err) : "",
                       error_message_verbatim: err ? err.message.strip : "")
      rec[:op] = "late_#{base[:op]}" unless mine
      write.call(rec)
    end
  end
end

interval = 1.0 / rate
start = Time.now.to_f
seq = 0
i = 0
loop do
  sched = start + i * interval
  break if sched - start >= dur
  d = sched - Time.now.to_f
  sleep d if d > 0
  op = i.even? ? "insert" : "select"
  s = nil
  if op == "insert"
    seq += 1
    s = seq
  end
  base = { ts: Time.at(sched).utc.iso8601(3), ts_ms: (sched * 1000).to_i, client: client, op: op, seq: s }
  mu.synchronize { outstanding[i] = [base, sched + timeout] }
  workers << [i, base]
  i += 1
end
sleep timeout + 0.2
stop = true
reaper.join
deadline = Time.now.to_f + 3
sleep 0.1 while !workers.empty? && Time.now.to_f < deadline
mu.synchronize { out.flush }
exit!(0)
