"""Server command line for the Trip Campus admin. Run with sudo:

  sudo tc-admin set-password           choose a new admin password (also signs out every session)
  sudo tc-admin set-email EMAIL        change the one admin login email
  sudo tc-admin publish                rebuild the website pages now
  sudo tc-admin test-email             send a test enquiry email
  sudo tc-admin status                 show settings (no secrets)
"""
import getpass, json, os, pwd, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app


def fix_owner():
    try:
        u = pwd.getpwnam('tripcampus')
        os.chown(app.CONFIG_FILE, u.pw_uid, u.pw_gid)
        for root, dirs, files in os.walk(app.CFG['data_dir']):
            for n in dirs + files:
                os.chown(os.path.join(root, n), u.pw_uid, u.pw_gid)
    except (KeyError, PermissionError):
        pass


def restart_hint():
    os.system('systemctl restart tripcampus 2>/dev/null')


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'help'
    app.init_db()
    if cmd == 'set-password':
        while True:
            a = getpass.getpass('New admin password (at least 10 characters): ')
            if len(a) < 10:
                print('Too short.'); continue
            if a != getpass.getpass('Repeat it: '):
                print('They do not match.'); continue
            break
        app.save_password(a); app.end_all_sessions(); fix_owner(); restart_hint()
        print('Password saved. Sign in at /admin/ with', app.CFG['admin_email'])
    elif cmd == 'set-email' and len(argv) > 2:
        cfg = json.load(open(app.CONFIG_FILE)); cfg['admin_email'] = argv[2].strip().lower()
        json.dump(cfg, open(app.CONFIG_FILE, 'w'), indent=1); app.end_all_sessions(); fix_owner(); restart_hint()
        print('Admin email is now', cfg['admin_email'])
    elif cmd == 'publish':
        r = app.publish('server'); fix_owner()
        print('Published %d pages in %ss %s' % (r['pages'], r['seconds'], r['warnings'] or ''))
    elif cmd == 'test-email':
        s = app.CFG['smtp']
        if not s.get('host'):
            print('Email is not set up. Edit the "smtp" section of', app.CONFIG_FILE); return
        import smtplib
        from email.message import EmailMessage
        m = EmailMessage(); m['Subject'] = 'Trip Campus test email'; m['From'] = s.get('from') or s['user']; m['To'] = s['to']
        m.set_content('Enquiry emails from the website are working.')
        with smtplib.SMTP(s['host'], int(s['port']), timeout=20) as srv:
            srv.starttls()
            if s.get('user'): srv.login(s['user'], s['password'])
            srv.send_message(m)
        print('Sent to', s['to'])
    elif cmd == 'status':
        c = app.CFG
        print('admin email :', c['admin_email'] or 'NOT SET')
        print('password    :', 'set' if c['password_hash'] else 'NOT SET')
        print('email alerts:', ('%s -> %s' % (c['smtp']['host'], c['smtp']['to'])) if c['smtp'].get('host') else 'not set up')
        print('website dir :', c['site_dir']); print('data dir    :', c['data_dir'])
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv)
