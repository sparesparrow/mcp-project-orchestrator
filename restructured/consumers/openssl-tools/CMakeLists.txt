cmake_minimum_required(VERSION 3.15)
project(OpenSSLToolsOrchestrator VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenSSL REQUIRED)
find_package(ZLIB REQUIRED)

# Include directories
include_directories(include)

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.c")
file(GLOB_RECURSE HEADERS "include/*.h" "include/*.hpp")

# Create library
add_library(openssl_tools_orchestrator ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(openssl_tools_orchestrator 
    OpenSSL::SSL 
    OpenSSL::Crypto 
    ZLIB::ZLIB
)

# FIPS support
if(FIPS_ENABLED)
    target_compile_definitions(openssl_tools_orchestrator PRIVATE FIPS_MODE=1)
    find_package(FIPSCrypto REQUIRED)
    target_link_libraries(openssl_tools_orchestrator FIPSCrypto::FIPSCrypto)
endif()

# Install
install(TARGETS openssl_tools_orchestrator
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
