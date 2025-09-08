cmake_minimum_required(VERSION 3.10)
project(XillenDoS)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(WIN32)
    add_library(dos_engine SHARED engine/dos_engine.cpp)
    target_link_libraries(dos_engine ws2_32)
else()
    add_library(dos_engine SHARED engine/dos_engine.cpp)
endif()

set_target_properties(dos_engine PROPERTIES
    OUTPUT_NAME "dos_engine"
    PREFIX ""
)

if(WIN32)
    set_target_properties(dos_engine PROPERTIES SUFFIX ".dll")
else()
    set_target_properties(dos_engine PROPERTIES SUFFIX ".so")
endif()