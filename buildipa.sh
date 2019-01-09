#!/bin/bash
docker-compose \
	--file docker-compose.ipabuild.yml \
	run ipa \
	exit-on-finished \
	--unattended \
	--no-host-dns \
	--setup-dns \
	--no-reverse \
	--auto-forwarders \
	--no-ntp \
	--no-ssh --no-sshd --no-dns-sshfp \
	--ds-password noggindev \
	--admin-password noggindev \
	--domain noggindev.local \
	--realm NOGGINDEV.LOCAL
