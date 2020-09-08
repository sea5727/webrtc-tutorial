cmake_minimum_required(VERSION 3.0.0)
project(myms VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost 1.73 REQUIRED COMPONENTS program_options system thread )
if (Boost_FOUND)
   # find_package( Boost REQUIRED COMPONENTS system date_time thread )
   include_directories(${Boost_INCLUDE_DIR})   

   include_directories(/usr/local/include)
   link_directories(/usr/local/lib)
   # include_directories(/usr/local/gcc/include)
   # link_directories(/usr/local/gcc/lib64)

   message(Boost_FOUND: ${Boost_FOUND} )
   message(Boost_INCLUDE_DIR: ${Boost_INCLUDE_DIR} )
   message(Boost_LIBRARY_DIRS: ${Boost_LIBRARY_DIRS} )
   message(Boost_LIBRARIES: ${Boost_LIBRARIES} )
   message(Boost_SYSTEM_FOUND: ${Boost_SYSTEM_FOUND} )
   message(Boost_SYSTEM_LIBRARY: ${Boost_SYSTEM_LIBRARY} )
   message(Boost_DATE_TIME_FOUND: ${Boost_DATE_TIME_FOUND} )
   message(Boost_DATE_TIME_LIBRARY: ${Boost_DATE_TIME_LIBRARY} )
   add_definitions( "-DHAS_BOOST" )
endif()

include_directories(/usr/include/gstreamer-1.0 /usr/include/glib-2.0 /usr/lib64/glib-2.0/include)   
link_libraries(gstsdp-1.0 glib-2.0 gstreamer-1.0 gobject-2.0)

include(CTest)
enable_testing()

include_directories(/usr/local/include)
link_directories(/usr/local/lib)
link_libraries(${Boost_LIBRARIES})

add_executable(webrtc-server main.cpp)


set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)
