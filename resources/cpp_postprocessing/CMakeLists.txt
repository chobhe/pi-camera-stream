cmake_minimum_required(VERSION 3.16)

# Name of your project
project(MyCppProject LANGUAGES CXX)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Export compile commands for clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# If you have headers in an "include" folder, add:
# include_directories(${CMAKE_SOURCE_DIR}/include)

# List all your .cpp files here
add_executable(my_app
    bounding_boxes.cpp
    helloworld.cpp
)