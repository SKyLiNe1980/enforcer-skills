# Hermes TUI vs CLI Auto-Resume

## The problem
`tui_auto_resume_recent: true` only works in TUI mode. Running in CLI mode (default) does NOT auto-resume sessions, even with `/save` before exit.

## Check which mode you're in
```bash
grep "interface:" ~/.hermes/config.yaml
```
- `interface: cli` → auto-resume does NOT work (must `/session resume` manually)
- `interface: tui` → auto-resume works if `tui_auto_resume_recent: true`

## Fix
```yaml
# In config.yaml
interface: tui
display:
  tui_auto_resume_recent: true
```

Or switch live: `/tui` in-session.

## Session conflict pitfall
The auto-resume picks the session with the **newest filesystem timestamp**, not the most recently active. If WhatsApp/Discord integrations write to their session files after your last `/save`, they'll get auto-resumed instead. Check with:
```
/session list
/session resume <number>
```
