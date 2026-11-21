// pgx v5 workload: open-loop requests through pgxpool with library defaults.
//
// Env: DATABASE_URL, CLIENT, RUN_TAG, RATE (req/s), DURATION_S, TIMEOUT_MS,
// OUT (JSONL path), PGX_CANCEL=default|cancelrequest.
//
// PGX_CANCEL=default keeps pgconn's default context watcher
// (DeadlineContextWatcherHandler: on ctx cancel it sets a past deadline on the
// socket, which makes pgx close the connection). PGX_CANCEL=cancelrequest
// installs CancelRequestContextWatcherHandler, which sends a Postgres
// CancelRequest and keeps the connection if the server answers in time.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgconn/ctxwatch"
	"github.com/jackc/pgx/v5/pgxpool"
)

type record struct {
	TS        string  `json:"ts"`
	TSMs      int64   `json:"ts_ms"`
	Client    string  `json:"client"`
	Op        string  `json:"op"`
	Seq       *int64  `json:"seq"`
	OK        bool    `json:"ok"`
	LatencyMs float64 `json:"latency_ms"`
	ErrClass  string  `json:"error_class"`
	ErrMsg    string  `json:"error_message_verbatim"`
	SQLState  string  `json:"sqlstate,omitempty"`
}

func envInt(k string, d int) int {
	if v, err := strconv.Atoi(os.Getenv(k)); err == nil {
		return v
	}
	return d
}

func classify(ctx context.Context, err error) (string, string) {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return "pg_" + pgErr.Code, pgErr.Code
	}
	if errors.Is(err, context.DeadlineExceeded) || ctx.Err() != nil {
		return "timeout", ""
	}
	if pgconn.Timeout(err) {
		return "timeout", ""
	}
	var opErr *net.OpError
	if errors.As(err, &opErr) {
		return "net_" + opErr.Op, ""
	}
	var dnsErr *net.DNSError
	if errors.As(err, &dnsErr) {
		return "dns", ""
	}
	return "other", ""
}

func main() {
	url := os.Getenv("DATABASE_URL")
	client := os.Getenv("CLIENT")
	tag := client + "/" + os.Getenv("RUN_TAG")
	rate := envInt("RATE", 50)
	dur := time.Duration(envInt("DURATION_S", 90)) * time.Second
	timeout := time.Duration(envInt("TIMEOUT_MS", 2000)) * time.Millisecond

	cfg, err := pgxpool.ParseConfig(url)
	if err != nil {
		log.Fatal(err)
	}
	switch os.Getenv("PGX_CANCEL") {
	case "", "default":
	case "cancelrequest":
		cfg.ConnConfig.BuildContextWatcherHandler = func(c *pgconn.PgConn) ctxwatch.Handler {
			return &pgconn.CancelRequestContextWatcherHandler{Conn: c, DeadlineDelay: time.Second}
		}
	default:
		log.Fatalf("PGX_CANCEL must be default or cancelrequest")
	}
	log.Printf("pgxpool: MaxConns=%d MinConns=%d DefaultQueryExecMode=%v HealthCheckPeriod=%v cancel=%q",
		cfg.MaxConns, cfg.MinConns, cfg.ConnConfig.DefaultQueryExecMode, cfg.HealthCheckPeriod, os.Getenv("PGX_CANCEL"))

	// The pool connects lazily; a failed initial connect is not fatal.
	pool, err := pgxpool.NewWithConfig(context.Background(), cfg)
	if err != nil {
		log.Fatal(err)
	}

	f, err := os.Create(os.Getenv("OUT"))
	if err != nil {
		log.Fatal(err)
	}
	out := make(chan record, 10000)
	done := make(chan struct{})
	go func() {
		enc := json.NewEncoder(f)
		for r := range out {
			enc.Encode(r)
		}
		f.Close()
		close(done)
	}()

	var seq int64
	var wg sync.WaitGroup
	interval := time.Second / time.Duration(rate)
	start := time.Now()
	for i := 0; ; i++ {
		sched := start.Add(time.Duration(i) * interval)
		if sched.Sub(start) >= dur {
			break
		}
		time.Sleep(time.Until(sched))
		wg.Add(1)
		go func(i int, sched time.Time) {
			defer wg.Done()
			r := record{TS: sched.UTC().Format(time.RFC3339Nano), TSMs: sched.UnixMilli(), Client: client}
			ctx, cancel := context.WithDeadline(context.Background(), sched.Add(timeout))
			defer cancel()
			var err error
			if i%2 == 0 {
				s := atomic.AddInt64(&seq, 1)
				r.Op, r.Seq = "insert", &s
				_, err = pool.Exec(ctx, "INSERT INTO ledger (client, seq, ts) VALUES ($1, $2, now())", tag, s)
			} else {
				r.Op = "select"
				var id int64
				err = pool.QueryRow(ctx, "SELECT coalesce(max(id), 0) FROM ledger").Scan(&id)
			}
			r.LatencyMs = float64(time.Since(sched).Microseconds()) / 1000
			if err == nil && r.LatencyMs > float64(timeout.Milliseconds()) {
				// Finished, but after the caller's deadline: not acknowledged.
				err = fmt.Errorf("completed after client deadline")
			}
			if err != nil {
				r.ErrClass, r.SQLState = classify(ctx, err)
				r.ErrMsg = err.Error()
			} else {
				r.OK = true
			}
			out <- r
		}(i, sched)
	}
	wg.Wait()
	close(out)
	<-done
	pool.Close()
}
