# Setting up Email

Proof Buddy sends emails for activating user accounts and resetting passwords. You need to set the `EMAIL_` environment variables so Proof Buddy can connect to an SMTP server. An easy approach is to use a GMail account. For example:

```ini
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=example@gmail.com
EMAIL_HOST_PASSWORD=abcd abcd abcd abcd
```

Replace `example@gmail.com` with your own GMail address. Use <https://myaccount.google.com/apppasswords> to set up a password for Proof Buddy. The `EMAIL_HOST_PASSWORD` is not the same password you use to log in to your GMail account normally.
