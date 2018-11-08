#!/bin/bash
docker-compose run ipa \
	exit-on-finished \
	--unattended \
	--ds-password noggindev \
	--admin-password noggindev \
	--domain noggindev.local \
	--realm NOGGINDEV.LOCAL
