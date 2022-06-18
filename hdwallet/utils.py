import threading


def multithreading_execute(list_of_task):
    threads = []
    for task in list_of_task:
        threads.append(threading.Thread(target=task))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
