#pragma once

#include <cinttypes>
#include <csignal>

#include "pthread.h"
#include "sys/types.h"

struct Address;

class ProxyServer {
   private:
    // for singleton
    static ProxyServer *proxyServer;

    char *host;
    int pull_port, push_port, pull_socket, push_socket;

    struct Address *address;
    struct Address *addressPush;

    // private constructor for singleton
    ProxyServer();

   public:
    char *exceptionMsg;

    static void startPushDebuggerSocket(struct Socket arg);

    void registerAddresses(char *_host, int _pull_port, int _push_port);
    void closeConnections();
    pthread_t openConnections(pthread_mutex_t *mutex);
    void updateExcpMsg(const char *msg);
    bool send(void *t_buffer, int t_size);
    char *readReply(short int amount = 1024);

    static void registerMCUHost(uint8_t **data);
    static ProxyServer *getServer();
};
