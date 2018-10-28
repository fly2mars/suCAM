// This file is part of libigl, a simple c++ geometry processing library.
//
// Copyright (C) 2018 Jérémie Dumas <jeremie.dumas@ens-lyon.org>
//
// This Source Code Form is subject to the terms of the Mozilla Public License
// v. 2.0. If a copy of the MPL was not distributed with this file, You can
// obtain one at http://mozilla.org/MPL/2.0/.
#pragma once

////////////////////////////////////////////////////////////////////////////////
#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/ViewerPlugin.h>
#include <igl/igl_inline.h>
////////////////////////////////////////////////////////////////////////////////


namespace igl
{
	namespace viewer
	{
		namespace glfw
		{			
			class Plugin_Load_Off : public igl::opengl::glfw::ViewerPlugin
			{
			protected:


			public:
				// This function is called before a mesh is loaded
				IGL_INLINE virtual bool load(std::string filename);

				void update();
			};

		} // end namespace
	} // end namespace
} // end namespace


#ifndef IGL_STATIC_LIBRARY
#  include "plugin_load_off.cpp"
#endif
