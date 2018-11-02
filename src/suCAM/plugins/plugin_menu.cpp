// This file is part of libigl, a simple c++ geometry processing library.
//
// Copyright (C) 2018 Jérémie Dumas <jeremie.dumas@ens-lyon.org>
//
// This Source Code Form is subject to the terms of the Mozilla Public License
// v. 2.0. If a copy of the MPL was not distributed with this file, You can
// obtain one at http://mozilla.org/MPL/2.0/.
////////////////////////////////////////////////////////////////////////////////
#include "../plugin_menu.h"
#include <igl/project.h>
#include <imgui/imgui.h>
#include <imgui_impl_glfw_gl3.h>
#include <imgui_fonts_droid_sans.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include <array>
#include "../suGlobalState.h"
////////////////////////////////////////////////////////////////////////////////



namespace ImGui
{
	
	//using combo and list with stl
	static auto vector_getter = [](void* vec, int idx, const char** out_text)
	{
		auto& vector = *static_cast<std::vector<std::string>*>(vec);
		if (idx < 0 || idx >= static_cast<int>(vector.size())) { return false; }
		*out_text = vector.at(idx).c_str();
		return true;
	};

	bool Combo(const char* label, int* currIndex, std::vector<std::string>& values)
	{
		if (values.empty()) { return false; }
		return Combo(label, currIndex, vector_getter,
			static_cast<void*>(&values), values.size());
	}

	bool ListBox(const char* label, int* currIndex, std::vector<std::string>& values)
	{
		if (values.empty()) { return false; }
		return ListBox(label, currIndex, vector_getter,
			static_cast<void*>(&values), values.size());
	}


}
namespace igl
{
	namespace opengl
	{
		namespace glfw
		{
			namespace imgui
			{

				IGL_INLINE void Plugin_Menu::init(igl::opengl::glfw::Viewer  *_viewer)
				{
					ViewerPlugin::init(_viewer);
					// Setup ImGui binding
					if (_viewer)
					{
						if (context_ == nullptr)
						{
							context_ = ImGui::CreateContext();
						}
						ImGui_ImplGlfwGL3_Init(viewer->window, false);
						ImGui::GetIO().IniFilename = nullptr;
						ImGui::StyleColorsDark();
						ImGuiStyle& style = ImGui::GetStyle();
						style.FrameRounding = 5.0f;
						reload_font();
					}
				}

				IGL_INLINE void Plugin_Menu::reload_font(int font_size)
				{
					hidpi_scaling_ = hidpi_scaling();
					pixel_ratio_ = pixel_ratio();
					ImGuiIO& io = ImGui::GetIO();
					io.Fonts->Clear();
					io.Fonts->AddFontFromMemoryCompressedTTF(droid_sans_compressed_data,
						droid_sans_compressed_size, font_size * hidpi_scaling_);
					io.FontGlobalScale = 1.0 / pixel_ratio_;
				}

				IGL_INLINE void Plugin_Menu::shutdown()
				{
					// Cleanup
					ImGui_ImplGlfwGL3_Shutdown();
					ImGui::DestroyContext(context_);
					context_ = nullptr;
				}

				IGL_INLINE bool Plugin_Menu::pre_draw()
				{
					glfwPollEvents();

					// Check whether window dpi has changed
					float scaling = hidpi_scaling();
					if (std::abs(scaling - hidpi_scaling_) > 1e-5)
					{
						reload_font();
						ImGui_ImplGlfwGL3_InvalidateDeviceObjects();
					}

					ImGui_ImplGlfwGL3_NewFrame();
					return false;
				}

				IGL_INLINE bool Plugin_Menu::post_draw()
				{
					draw_menu();
					ImGui::Render();
					return false;
				}

				IGL_INLINE void Plugin_Menu::post_resize(int width, int height)
				{
					if (context_)
					{
						ImGui::GetIO().DisplaySize.x = float(width);
						ImGui::GetIO().DisplaySize.y = float(height);
					}
				}

				// Mouse IO
				IGL_INLINE bool Plugin_Menu::mouse_down(int button, int modifier)
				{
					ImGui_ImplGlfwGL3_MouseButtonCallback(viewer->window, button, GLFW_PRESS, modifier);
					return ImGui::GetIO().WantCaptureMouse;
				}

				IGL_INLINE bool Plugin_Menu::mouse_up(int button, int modifier)
				{
					return ImGui::GetIO().WantCaptureMouse;
				}

				IGL_INLINE bool Plugin_Menu::mouse_move(int mouse_x, int mouse_y)
				{
					return ImGui::GetIO().WantCaptureMouse;
				}

				IGL_INLINE bool Plugin_Menu::mouse_scroll(float delta_y)
				{
					ImGui_ImplGlfwGL3_ScrollCallback(viewer->window, 0.f, delta_y);
					return ImGui::GetIO().WantCaptureMouse;
				}

				// Keyboard IO
				IGL_INLINE bool Plugin_Menu::key_pressed(unsigned int key, int modifiers)
				{
					ImGui_ImplGlfwGL3_CharCallback(nullptr, key);
					return ImGui::GetIO().WantCaptureKeyboard;
				}

				IGL_INLINE bool Plugin_Menu::key_down(int key, int modifiers)
				{
					ImGui_ImplGlfwGL3_KeyCallback(viewer->window, key, 0, GLFW_PRESS, modifiers);
					return ImGui::GetIO().WantCaptureKeyboard;
				}

				IGL_INLINE bool Plugin_Menu::key_up(int key, int modifiers)
				{
					ImGui_ImplGlfwGL3_KeyCallback(viewer->window, key, 0, GLFW_RELEASE, modifiers);
					return ImGui::GetIO().WantCaptureKeyboard;
				}

				// Draw menu
				IGL_INLINE void Plugin_Menu::draw_menu()
				{
					// Text labels
					draw_labels_window();

					// Viewer settings
					if (callback_draw_viewer_window) { callback_draw_viewer_window(); }
					else { draw_viewer_window(); }

					// Other windows
					if (callback_draw_custom_window) { callback_draw_custom_window(); }
					else { draw_custom_window(); }
				}

				IGL_INLINE void Plugin_Menu::draw_viewer_window()
				{
					float menu_width = 180.f * menu_scaling();
					ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f), ImGuiSetCond_FirstUseEver);
					ImGui::SetNextWindowSize(ImVec2(0.0f, 0.0f), ImGuiSetCond_FirstUseEver);
					ImGui::SetNextWindowSizeConstraints(ImVec2(menu_width, -1.0f), ImVec2(menu_width, -1.0f));
					bool _viewer_menu_visible = true;
					ImGui::Begin(
						"Viewer", &_viewer_menu_visible,
						ImGuiWindowFlags_NoSavedSettings
						| ImGuiWindowFlags_AlwaysAutoResize
					);
					ImGui::PushItemWidth(ImGui::GetWindowWidth() * 0.4f);
					if (callback_draw_viewer_menu) { callback_draw_viewer_menu(); }
					else { draw_viewer_menu(); }
					ImGui::PopItemWidth();
					ImGui::End();
				}

				/*
				* Show tip for each widget. 
				*/
				static void ShowHelpMarker(const char* desc)
				{
					ImGui::TextDisabled("(?)");
					if (ImGui::IsItemHovered())
					{
						ImGui::BeginTooltip();
						ImGui::PushTextWrapPos(ImGui::GetFontSize() * 35.0f);
						ImGui::TextUnformatted(desc);
						ImGui::PopTextWrapPos();
						ImGui::EndTooltip();
					}
				}

				

				IGL_INLINE void Plugin_Menu::draw_viewer_menu()
				{
					// Workspace
					/*if (ImGui::CollapsingHeader("Workspace", ImGuiTreeNodeFlags_DefaultOpen))
					{
						float w = ImGui::GetContentRegionAvailWidth();
						float p = ImGui::GetStyle().FramePadding.x;
						if (ImGui::Button("Load##Workspace", ImVec2((w - p) / 2.f, 0)))
						{
							viewer->load_scene();
						}
						ImGui::SameLine(0, p);
						if (ImGui::Button("Save##Workspace", ImVec2((w - p) / 2.f, 0)))
						{
							viewer->save_scene();
						}
					}*/


					// Mesh
					if (ImGui::CollapsingHeader("Mesh", ImGuiTreeNodeFlags_DefaultOpen))
					{
						float w = ImGui::GetContentRegionAvailWidth();
						float p = ImGui::GetStyle().FramePadding.x;
						if (ImGui::Button("Load##Mesh", ImVec2((w - p) / 2.f, 0)))
						{
							viewer->open_dialog_load_mesh();
						}
						ImGui::SameLine(0, p);
						if (ImGui::Button("Save##Mesh", ImVec2((w - p) / 2.f, 0)))
						{
							viewer->open_dialog_save_mesh();
						}
						// Typically we would use ImVec2(-1.0f,0.0f) to use all available width, or ImVec2(width,0.0f) for a specified width. ImVec2(0.0f,0.0f) uses ItemWidth.
						ImGui::ProgressBar(suGlobalState::gOnly().progress, ImVec2(-1.0f, 0.0f));
						//ImGui::SameLine(0.0f, ImGui::GetStyle().ItemInnerSpacing.x);
						//ImGui::Text("Progress Bar");

					}

					// Customized menu
					if (ImGui::CollapsingHeader("Selection Menu", ImGuiTreeNodeFlags_DefaultOpen))
					{
						/*float w = ImGui::GetContentRegionAvailWidth();
						float p = ImGui::GetStyle().FramePadding.x;*/

						ImGui::Text("Object Label Management");
						
						static char str0[128] = "";
						ImGui::InputText("##ObjectLabel", str0, IM_ARRAYSIZE(str0));
						ImGui::SameLine();
						if (ImGui::Button("Add Label", ImVec2(-1, 0)))
						{
							suGlobalState::gOnly().object_labels.push_back(str0);
							std::cout << str0 << std::endl;
						}

						//Comb object labels
						{
							ImGui::Combo("##object_labels", &(suGlobalState::gOnly().cur_index_of_object_label), 
								suGlobalState::gOnly().object_labels);
							ImGui::SameLine(); //ShowHelpMarker("Specify an object label for your choose\n");
							ImGui::Checkbox("Object", &suGlobalState::gOnly().b_label_item[0]);
						}
						if (suGlobalState::gOnly().b_label_item[0])   suGlobalState::gOnly().b_label_item[1] = 0;
						//				
						//ImGui::SameLine();
						ImGui::Text("Surface Label Management");

						static char str1[128] = "";
						ImGui::InputText("##SurfaceLabel", str1, IM_ARRAYSIZE(str1));
						ImGui::SameLine();
						if (ImGui::Button("Add Label##surface", ImVec2(-1, 0)))
						{
							suGlobalState::gOnly().surface_labels.push_back(str1);
							std::cout << str1 << std::endl;
						}
						//Comb surface labels
						{
							
							ImGui::Combo("##surface_labels", &(suGlobalState::gOnly().cur_index_of_surface_label), 
								suGlobalState::gOnly().surface_labels);
							ImGui::SameLine(); //ShowHelpMarker("Specify a surface label for your choose\n");
							ImGui::Checkbox("Surface", &suGlobalState::gOnly().b_label_item[1]);
						}

						if (suGlobalState::gOnly().b_label_item[1])   suGlobalState::gOnly().b_label_item[0] = 0;
						

						//
						ImGui::Text("Propagation parameters:");
						ImGui::Indent();
						ImGui::DragFloat("Angle", &(suGlobalState::gOnly().max_angle_between_face_normal), 0.01f, 0.0f, 180.0f, "%.1f");
						ImGui::SameLine(); ShowHelpMarker("Angle  between triangle");
						ImGui::DragFloat("Curvature", &(suGlobalState::gOnly().max_curvature_between_face), 0.01f, 0.0f, 180.0f, "%.1f");
						ImGui::SameLine(); ShowHelpMarker("Curvature  between triangle");						
						ImGui::Unindent();
					}


					// Viewing options
					if (ImGui::CollapsingHeader("Viewing Options", ImGuiTreeNodeFlags_DefaultOpen))
					{
						if (ImGui::Button("Center object", ImVec2(-1, 0)))
						{
							viewer->core.align_camera_center(viewer->data().V, viewer->data().F);
						}
						if (ImGui::Button("Snap canonical view", ImVec2(-1, 0)))
						{
							viewer->snap_to_canonical_quaternion();
						}

						// Zoom
						ImGui::PushItemWidth(80 * menu_scaling());
						ImGui::DragFloat("Zoom", &(viewer->core.camera_zoom), 0.05f, 0.1f, 20.0f);

						// Select rotation type
						int rotation_type = static_cast<int>(viewer->core.rotation_type);
						static Eigen::Quaternionf trackball_angle = Eigen::Quaternionf::Identity();
						static bool orthographic = true;
						if (ImGui::Combo("Camera Type", &rotation_type, "Trackball\0Two Axes\0002D Mode\0\0"))
						{
							using RT = igl::opengl::ViewerCore::RotationType;
							auto new_type = static_cast<RT>(rotation_type);
							if (new_type != viewer->core.rotation_type)
							{
								if (new_type == RT::ROTATION_TYPE_NO_ROTATION)
								{
									trackball_angle = viewer->core.trackball_angle;
									orthographic = viewer->core.orthographic;
									viewer->core.trackball_angle = Eigen::Quaternionf::Identity();
									viewer->core.orthographic = true;
								}
								else if (viewer->core.rotation_type == RT::ROTATION_TYPE_NO_ROTATION)
								{
									viewer->core.trackball_angle = trackball_angle;
									viewer->core.orthographic = orthographic;
								}
								viewer->core.set_rotation_type(new_type);
							}
						}

						// Orthographic view
						ImGui::Checkbox("Orthographic view", &(viewer->core.orthographic));
						ImGui::PopItemWidth();
					}

					// Draw options
					if (ImGui::CollapsingHeader("Draw Options", ImGuiTreeNodeFlags_DefaultOpen))
					{
						if (ImGui::Checkbox("Face-based", &(viewer->data().face_based)))
						{
							viewer->data().set_face_based(viewer->data().face_based);
						}
						ImGui::Checkbox("Show texture", &(viewer->data().show_texture));
						if (ImGui::Checkbox("Invert normals", &(viewer->data().invert_normals)))
						{
							viewer->data().dirty |= igl::opengl::MeshGL::DIRTY_NORMAL;
						}
						ImGui::Checkbox("Show overlay", &(viewer->data().show_overlay));
						ImGui::Checkbox("Show overlay depth", &(viewer->data().show_overlay_depth));
						ImGui::ColorEdit4("Background", viewer->core.background_color.data(),
							ImGuiColorEditFlags_NoInputs | ImGuiColorEditFlags_PickerHueWheel);
						ImGui::ColorEdit4("Line color", viewer->data().line_color.data(),
							ImGuiColorEditFlags_NoInputs | ImGuiColorEditFlags_PickerHueWheel);
						ImGui::PushItemWidth(ImGui::GetWindowWidth() * 0.3f);
						ImGui::DragFloat("Shininess", &(viewer->data().shininess), 0.05f, 0.0f, 100.0f);
						ImGui::PopItemWidth();
					}

					// Overlays
					if (ImGui::CollapsingHeader("Overlays", ImGuiTreeNodeFlags_DefaultOpen))
					{
						ImGui::Checkbox("Wireframe", &(viewer->data().show_lines));
						ImGui::Checkbox("Fill", &(viewer->data().show_faces));
						ImGui::Checkbox("Show vertex labels", &(viewer->data().show_vertid));
						ImGui::Checkbox("Show faces labels", &(viewer->data().show_faceid));
					}
				}

				IGL_INLINE void Plugin_Menu::draw_labels_window()
				{
					// Text labels
					ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiSetCond_Always);
					ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize, ImGuiSetCond_Always);
					bool visible = true;
					ImGui::PushStyleColor(ImGuiCol_WindowBg, ImVec4(0, 0, 0, 0));
					ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0);
					ImGui::Begin("ViewerLabels", &visible,
						ImGuiWindowFlags_NoTitleBar
						| ImGuiWindowFlags_NoResize
						| ImGuiWindowFlags_NoMove
						| ImGuiWindowFlags_NoScrollbar
						| ImGuiWindowFlags_NoScrollWithMouse
						| ImGuiWindowFlags_NoCollapse
						| ImGuiWindowFlags_NoSavedSettings
						| ImGuiWindowFlags_NoInputs);
					for (const auto & data : viewer->data_list)
					{
						draw_labels(data);
					}
					ImGui::End();
					ImGui::PopStyleColor();
					ImGui::PopStyleVar();
				}

				IGL_INLINE void Plugin_Menu::draw_labels(const igl::opengl::ViewerData &data)
				{
					if (data.show_vertid)
					{
						for (int i = 0; i < data.V.rows(); ++i)
						{
							draw_text(data.V.row(i), data.V_normals.row(i), std::to_string(i));
						}
					}

					if (data.show_faceid)
					{
						for (int i = 0; i < data.F.rows(); ++i)
						{
							Eigen::RowVector3d p = Eigen::RowVector3d::Zero();
							for (int j = 0; j < data.F.cols(); ++j)
							{
								p += data.V.row(data.F(i, j));
							}
							p /= (double)data.F.cols();

							draw_text(p, data.F_normals.row(i), std::to_string(i));
						}
					}

					if (data.labels_positions.rows() > 0)
					{
						for (int i = 0; i < data.labels_positions.rows(); ++i)
						{
							draw_text(data.labels_positions.row(i), Eigen::Vector3d(0.0, 0.0, 0.0),
								data.labels_strings[i]);
						}
					}
				}

				IGL_INLINE void Plugin_Menu::draw_text(Eigen::Vector3d pos, Eigen::Vector3d normal, const std::string &text)
				{
					Eigen::Matrix4f view_matrix = viewer->core.view * viewer->core.model;
					pos += normal * 0.005f * viewer->core.object_scale;
					Eigen::Vector3f coord = igl::project(Eigen::Vector3f(pos.cast<float>()),
						view_matrix, viewer->core.proj, viewer->core.viewport);

					// Draw text labels slightly bigger than normal text
					ImDrawList* drawList = ImGui::GetWindowDrawList();
					drawList->AddText(ImGui::GetFont(), ImGui::GetFontSize() * 1.2,
						ImVec2(coord[0] / pixel_ratio_, (viewer->core.viewport[3] - coord[1]) / pixel_ratio_),
						ImGui::GetColorU32(ImVec4(0, 0, 10, 255)),
						&text[0], &text[0] + text.size());
				}

				IGL_INLINE float Plugin_Menu::pixel_ratio()
				{
					// Computes pixel ratio for hidpi devices
					int buf_size[2];
					int win_size[2];
					GLFWwindow* window = glfwGetCurrentContext();
					glfwGetFramebufferSize(window, &buf_size[0], &buf_size[1]);
					glfwGetWindowSize(window, &win_size[0], &win_size[1]);
					return (float)buf_size[0] / (float)win_size[0];
				}

				IGL_INLINE float Plugin_Menu::hidpi_scaling()
				{
					// Computes scaling factor for hidpi devices
					float xscale, yscale;
					GLFWwindow* window = glfwGetCurrentContext();
					glfwGetWindowContentScale(window, &xscale, &yscale);
					return 0.5 * (xscale + yscale);
				}

			} // end namespace
		} // end namespace
	} // end namespace
} // end namespace
