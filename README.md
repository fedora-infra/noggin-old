# noggin

Account System


## Development environment

The supported development environment is with `docker-compose`.

To prepare, you will probably need to run: `sudo setsebool -P container_manage_cgroup 1`.
This is needed since the FreeIPA container runs systemd to control services.

Now, to prepare the IPA server, run: `docker-compose up ipa`.
Wait until that prints that IPA is setup, and then control-c that.

Now, and any future times, you can run `docker-compose up`, and it should bring up IPA,
Ipsilon, CAIAPI, noggin and a utility container.

Run `docker-compose exec util myip` to determine the IP address of the utility container.
You can now connect to VNC on `utilip:5901` with password `noggindev` to access a
Firefox instance that has access to all the web services.
