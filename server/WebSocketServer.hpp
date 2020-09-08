#ifndef __WEB_SOCKET_SERVER_HPP__
#define __WEB_SOCKET_SERVER_HPP__

#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>
#include <rapidjson/document.h>

#include <boost/bind/bind.hpp>

#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

typedef websocketpp::server<websocketpp::config::asio> server;
typedef server::message_ptr message_ptr;

class WebSocketServer
{
public:
    boost::asio::io_service &_io_service;
    server web_socket_server;
public:
    WebSocketServer(boost::asio::io_service & io_service)
        : _io_service(io_service)
    {

    }


    void listen(uint16_t port)
    {
        web_socket_server.set_access_channels(websocketpp::log::alevel::all);
        web_socket_server.clear_access_channels(websocketpp::log::alevel::frame_payload);

        web_socket_server.init_asio(&_io_service);
        
        web_socket_server.set_message_handler(boost::bind(&WebSocketServer::on_message, this, boost::placeholders::_1, boost::placeholders::_2));
        boost::asio::ip::tcp::endpoint endpoint(boost::asio::ip::tcp::v4(), port);
        web_socket_server.set_reuse_addr(true);
        web_socket_server.listen(endpoint);
        web_socket_server.start_accept();

    }
    void on_message(websocketpp::connection_hdl hdl, message_ptr msg)
    {
        std::cout << "on_message:" << msg->get_payload() << std::endl;

        if (msg->get_payload() == "stop-listening") {
            web_socket_server.stop_listening();
            return;
        }

        // rapidjson::Document document;

        // document.Parse(msg->get_payload().c_str());




    }
};


#endif