cmake_minimum_required(VERSION 3.14)
project(VisionPyramidCppEngine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release)

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -mavx2 -mfma -ffast-math -flto")

add_executable(vision_cpp_engine
    src/main.cpp
    src/vision_pyramid.cpp
)

target_include_directories(vision_cpp_engine PRIVATE src)
