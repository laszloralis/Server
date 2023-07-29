import concurrent.futures
from time import sleep

import wordpress_io as wp_io
import protocol_io as p_io


from performance_timer import PerformanceTimer


# #########################################################################
# main_loop()
# #########################################################################
def main_loop():
    print('Wordpress client is running')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            # time-measurement start
            wp_client_pt = PerformanceTimer("wp_client")
            wp_client_pt.start()
            # Call WordPress client
            wp_io.client(executor)
            # time-measurement end
            wp_client_pt.print_duration(True)

            # Broadcast (new/changed/deleted items)...
            #p_io.protocol_object.notify_clients()

            # If every post received then go to sleep (see UPDATE_PERIOD, default is ~10 sec)
            # otherwise sleep 0.1 sec
            if wp_io.is_ready():
                sleep(wp_io.UPDATE_PERIOD)
            else:
                sleep(0.1)


# #########################################################################
# main
# #########################################################################
def main():
    print('start wordpress client...')
    # submit the 'mail_loop' task to the thread pool and get a future object
    with concurrent.futures.ThreadPoolExecutor(1) as executor:
        future = executor.submit(main_loop)
        # for debug...
        sleep(0.250)

        # wp_io.client should run...
        if not future.running():
            print('wordpress client could not start')
            exit(-1)

        print('start websocket server...')
        # Start the WS server and loop forever
        p_io.protocol_object.infinite_io_loop()


# =========================================================================
# ENTRY POINT
# =========================================================================
if __name__ == '__main__':
    main()
