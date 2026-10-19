# Web Terminal — HTTP interface per active slot

- `WebTerminal.hpp` / `.cpp`: minimal embedded HTTP endpoint, non-blocking (`WebTerminal_tick()`)
- Only responds when `WebTerminal_is_running()` (WiFi + active framework)
- JSON: `{"active":<slot>,"concurrent":<n>,"dual":true/false,"slots_ok":1}`
- Defensive: no RF interference; safe truncation (`512` byte buffer); 0 TODO/FIXME
- Access: connect to active framework's WiFi; manage via `/` endpoint (shows slot + concurrent state)
