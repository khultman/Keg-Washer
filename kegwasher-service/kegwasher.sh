#!/bin/sh
### BEGIN INIT INFO
# Provides:          kegwasher
# Required-Start:    $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Interrupt-based GPIO LED/pushbutton daemon
# Description:       Listens for button events and lights up LEDs
### END INIT INFO

# Do NOT "set -e"

# PATH should only include /usr/* if it runs after the mountnfs.sh script
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="kegwasher daemon"
NAME=kegwasher
#DAEMON=/usr/bin/$NAME
DAEMON=/home/pi/kegwasher-service/src/kegwasher.py
ARGS=""
PIDFILE=/var/run/${NAME}.pid
SCRIPTNAME=/etc/init.d/${NAME}
LOG_LEVEL=DEBUG

export QUIET=1

# Exit if the package is not installed
[ -x "${DAEMON}" ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/${NAME} ] && . /etc/default/${NAME}

# work out daemon args

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.2-14) to ensure that this file is present
# and status_of_proc is working.
. /lib/lsb/init-functions

#
# Function that starts the daemon/service
#
do_start()
{
	# Return
	#   0 if daemon has been started
	#   1 if daemon was already running
	#   2 if daemon could not be started

	start-stop-daemon --start --quiet --pidfile ${PIDFILE} --user root --exec ${DAEMON} --test > /dev/null \
		|| return 1

	start-stop-daemon --start --quiet --pidfile ${PIDFILE} --user root --make-pidfile --background --no-close --exec ${DAEMON} -- \
		${ARGS} \
		|| return 2
        sleep 1
}

#
# Function that stops the daemon/service
#
do_stop()
{
	# Return
	#   0 if daemon has been stopped
	#   1 if daemon was already stopped
	#   2 if daemon could not be stopped
	#   other if a failure occurred
	start-stop-daemon --stop --retry=TERM/30/KILL/5 --pidfile ${PIDFILE} --user root #--exec $DAEMON # don't pass --exec since is /usr/bin/python for scripts
	RETVAL="$?"
	[ "${RETVAL}" = 2 ] && return 2
        sleep 1
	# Many daemons don't delete their pidfiles when they exit.
	rm -f ${PIDFILE}
	return "${RETVAL}"
}

case "$1" in
  start)
	[ "${VERBOSE}" != no ] && log_daemon_msg "Starting ${DESC}" "${NAME}"
	do_start
	case "$?" in
		0|1) [ "${VERBOSE}" != no ] && log_end_msg 0 ;;
		2) [ "${VERBOSE}" != no ] && log_end_msg 1 ;;
	esac
	;;
  stop)
	[ "${VERBOSE}" != no ] && log_daemon_msg "Stopping ${DESC}" "${NAME}"
	do_stop
	case "$?" in
		0|1) [ "${VERBOSE}" != no ] && log_end_msg 0 ;;
		2) [ "${VERBOSE}" != no ] && log_end_msg 1 ;;
	esac
	;;
  status)
	status_of_proc "${DAEMON}" "${NAME}" && exit 0 || exit $?
	;;
  restart|force-reload)
	log_daemon_msg "Restarting ${DESC}" "${NAME}"
	do_stop
	case "$?" in
	  0|1)
		do_start
		case "$?" in
			0) log_end_msg 0 ;;
			1) log_end_msg 1 ;; # Old process is still running
			*) log_end_msg 1 ;; # Failed to start
		esac
		;;
	  *)
		# Failed to stop
		log_end_msg 1
		;;
	esac
	;;
  *)
	echo "Usage: ${SCRIPTNAME} {start|stop|status|restart|force-reload}" >&2
	exit 3
	;;
esac

: