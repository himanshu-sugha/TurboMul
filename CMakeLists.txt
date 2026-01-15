cmake_minimum_required(VERSION 3.10)
project(riscv_matmul_solver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Option to enable RISC-V cross-compilation
option(RISCV_CROSS "Cross-compile for RISC-V" OFF)

if(RISCV_CROSS)
    message(STATUS "Cross-compiling for RISC-V 64-bit")
    set(CMAKE_C_COMPILER riscv64-linux-gnu-gcc)
    set(CMAKE_CXX_COMPILER riscv64-linux-gnu-g++)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=rv64gcv -mabi=lp64d -Wall -Wextra")
else()
    message(STATUS "Building for native architecture (local testing)")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -Wall -Wextra")
endif()

# Locate OpenBLAS
find_library(OPENBLAS_LIB openblas)

if(OPENBLAS_LIB)
    message(STATUS "Found OpenBLAS: ${OPENBLAS_LIB}")
    add_definitions(-DUSE_OPENBLAS)
else()
    message(WARNING "OpenBLAS not found. Benchmarks will only run local implementations.")
endif()

# Sources
set(SOURCES
    main.cpp
    matmul_naive.cpp
    matmul_optimized.cpp
)

# Executable
add_executable(riscv_solver ${SOURCES})

# Link libraries
if(OPENBLAS_LIB)
    target_link_libraries(riscv_solver ${OPENBLAS_LIB})
else()
    target_link_libraries(riscv_solver pthread) # fallback
endif()
