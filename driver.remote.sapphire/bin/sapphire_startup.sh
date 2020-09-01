#!/storage/.kodi/addons/driver.remote.sapphire/bin/bash
#
# Some distros seem to be building the hid-topseed driver into
# the core kernel image, rather than leaving as a loadable module.
#
# So, for our sapphire driver to bind to a device,
# we first have to get the hid-topseed driver to unbind from it.
#
TOPSEED=/sys/bus/hid/drivers/topseed
SAPPHIRE=/sys/bus/hid/drivers/sapphire
rmmod hid-topseed	&>/dev/null
insmod /storage/.kodi/addons/driver.remote.sapphire/lib/sapphire.ko	&>/dev/null
if [ -d $SAPPHIRE -a -e $TOPSEED/unbind ]; then
	cd $TOPSEED
	for dev in [0-9]*[-0-9A-F] ; do
		if [ -e "$dev" ]; then
			echo "$dev" > unbind
			echo "$dev" > $SAPPHIRE/bind
		fi
	done
fi
#
# Ubuntu/Mint kernels (and likely others too) don't like it
# when we unload and reload the sapphire driver.
# They disable the USB IR receiver and fail to reenable it.
# The workaround below seems to restore functionality.
#
cd $SAPPHIRE || exit 1
for dev in [0-9]*[0-9A-F] ; do
	if [ -e "$dev" ]; then
		if cd -P "$dev/../.." ; then
			if [ -e authorized ]; then
				echo 0 > authorized
				echo 1 > authorized
			fi
			cd - >/dev/null
		fi
	fi
done
[ -e /storage/.kodi/userdata/addon_data/driver.remote.sapphire/sapphire.keymap -a -x /storage/.kodi/addons/driver.remote.sapphire/bin/sapphire_keymap.sh ] && /storage/.kodi/addons/driver.remote.sapphire/bin/sapphire_keymap.sh /storage/.kodi/userdata/addon_data/driver.remote.sapphire/sapphire.keymap
exit 0
