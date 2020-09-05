
#include <iostream>
#include <boost/asio.hpp>
#include "WebSocketServer.hpp"

int main(int argc, char *argv[])
{
    boost::asio::io_service _io_service;
    std::cout << "helloworld\n";
    WebSocketServer server(_io_service);


    server.listen(12345);


    _io_service.run();
    std::cout << "helloworld end\n";
    return 0;
}