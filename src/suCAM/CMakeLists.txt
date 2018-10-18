get_filename_component(PROJECT_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
project(${PROJECT_NAME})

#### project sources
FILE(GLOB SRC_SOURCES	${CMAKE_CURRENT_SOURCE_DIR}/*.cpp  )
FILE(GLOB SRC_HEADERS	${CMAKE_CURRENT_SOURCE_DIR}/*.h )
set(SRC_LIST ${SRC_SOURCES} ${SRC_HEADERS}  )

set(PROJECT_INCLUDE_DIRS ${CMAKE_SOURCE_DIR}/include)
set(PROJECT_LIBRARY_DIRS ${CMAKE_SOURCE_DIR}/lib)

include_directories(
  ${PROJECT_INCLUDE_DIRS}
  )

link_directories(
  ${PROJECT_LIBRARY_DIRS})



### APP
add_executable (${PROJECT_NAME}  ${SRC_LIST} )
target_link_libraries (${PROJECT_NAME}                     
  # Alias of target igl_core because it looks nicer[by using add_libary(igl::${module_name} ALIAS igl_${module_name}]
  igl::core igl::opengl_glfw    igl::opengl_glfw_imgui            
)


if (WIN32)
    set_property(TARGET ${PROJECT_NAME} PROPERTY FOLDER "Apps")
    configure_file(${CMAKE_SOURCE_DIR}/shared/vc/UnitTest.vcxproj.user
        ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.vcxproj.user @ONLY)
    # Properties->General->Output Directory
    set_property(TARGET ${PROJECT_NAME} PROPERTY RUNTIME_OUTPUT_DIRECTORY_RELEASE ${PROJECT_BINARY_DIR}/$(Platform)/$(Configuration))
    set_property(TARGET ${PROJECT_NAME} PROPERTY RUNTIME_OUTPUT_DIRECTORY_DEBUG ${PROJECT_BINARY_DIR}/$(Platform)/$(Configuration))
endif (WIN32)

# set the final binary dir
#set(PROJECT_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)

# copy binary to running director
#ADD_CUSTOM_COMMAND(TARGET ${APP_NAME}
#          POST_BUILD          
#          COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:${APP_NAME}> ${PROJECT_BINARY_DIR}
#)
