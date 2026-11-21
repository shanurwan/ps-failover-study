# Round `slot-failover`

Expected for a slot that continued correctly: `pre-unconsumed-1 pre-unconsumed-2 pre-unconsumed-3 pre-unconsumed-4 pre-unconsumed-5 post-1 post-2 post-3 post-4 post-5`.

| run | slot | standby sync wait (s) | exists on new primary | changes read after switchover | error |
|---|---|---|---|---|---|
| sync-off | sf_failover | - | False | `` |  |
| sync-on | sf_failover | 3 | True | `post-1 post-2 post-3 post-4 post-5 pre-unconsumed-1 pre-unconsumed-2 pre-unconsumed-3 pre-unconsumed-4 pre-unconsumed-5` |  |
| sync-on | sf_nofailover | 3 | False | `` |  |
