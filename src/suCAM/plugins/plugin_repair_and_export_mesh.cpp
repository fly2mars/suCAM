#pragma once

#include "../suGlobalState.h"
#include <igl/list_to_matrix.h>
#include "plugin_repair_and_export_mesh.h"

namespace igl
{
	namespace viewer
	{
		namespace glfw
		{

			class CmpVec
			{
			public:

				CmpVec(float _eps = FLT_MIN) : eps_(_eps) {}

				bool operator()(const std::vector<double> & _v0, const std::vector<double> & _v1) const
				{
					assert(_v0.size() == 3);
					assert(_v1.size() == 3);
					if (fabs(_v0[0] - _v1[0]) <= eps_)
					{
						if (fabs(_v0[1] - _v1[1]) <= eps_)
						{
							return (_v0[2] < _v1[2] - eps_);
						}
						else return (_v0[1] < _v1[1] - eps_);
					}
					else return (_v0[0] < _v1[0] - eps_);
				}

			private:
				float eps_;
			};

			IGL_INLINE bool plugin_repair_and_export::key_down(int key, int modifiers)
			{
				if (key == 'W')
				{

					segment_mesh(suGlobalState::gOnly().label_matrix, viewer->data().F, viewer->data().V);
				}
				return false;

			}


			//internal func
			bool plugin_repair_and_export::segment_mesh(Eigen::MatrixXd &label_matrix, Eigen::MatrixXi &F, Eigen::MatrixXd V)
			{
				int iObjectLabel;

				//segment F into Fs[object_label]
				for (int i = 0; i < label_matrix.rows(); i++)
				{
					iObjectLabel = label_matrix(i, 0);
					Face f;
					for (int j = 0; j < 3; j++)
					{
						f.push_back(F.row(i)(j));
					}

					Fs[iObjectLabel].push_back(f);
				}
				if (Fs.size() == 1) return false;

				//colors
				bool has_vert_color = false;
				Eigen::MatrixXd &C = suGlobalState::gOnly().C;
				if (C.size() == V.size())
				{
					has_vert_color = true;
				}
				//segment V into V_subset
				std::map<int, Faces>::iterator it;
				int nObjects = suGlobalState::gOnly().object_labels.size();

				//std::cout << V << std::endl;
				for (int iLabel = 0; iLabel < nObjects; iLabel++)
				{
					//for each segmented mesh
					if (Fs.count(iLabel) == 0)  continue;
					Faces fSet = Fs[iLabel];
					Verts vSet;
					std::vector<Color> cSet;
					std::map<Vert, Eigen::DenseIndex, CmpVec>  vMap;
					std::map<Vert, Eigen::DenseIndex, CmpVec>::iterator vMapIt;
					std::map<Eigen::DenseIndex, Eigen::DenseIndex> idxMap;   //combine index of same vertice, idxMap[i] = real index
					for (int i = 0; i < fSet.size(); i++)
					{
						//for each face

						Face &f = fSet[i];
						for (int j = 0; j < 3; j++)
						{
							Vert v;
							Eigen::DenseIndex vid = f[j];
							v.push_back(V.row(vid)(0));
							v.push_back(V.row(vid)(1));
							v.push_back(V.row(vid)(2));

							//update verts' index for each face 
							vMapIt = vMap.find(v);
							if (vMapIt != vMap.end())
							{
								f[j] = vMapIt->second;
							}
							else
							{
								int vert_idx = vMap.size();
								vMap[v] = vert_idx;
								f[j] = vert_idx;
								vSet.push_back(v);
								if (has_vert_color)
								{
									Color c;
									c.push_back(C.row(vid)(0));
									c.push_back(C.row(vid)(1));
									c.push_back(C.row(vid)(2));
									cSet.push_back(c);
								}
							}
							
						}

					}
					Eigen::MatrixXd V_subset;
					Eigen::MatrixXi F_subset;
					Eigen::MatrixXd C_subset;
					bool C_rect = igl::list_to_matrix(vSet, V_subset);
					if (!C_rect)
					{
						return false;
					}
					C_rect = igl::list_to_matrix(fSet, F_subset);
					if (!C_rect)
					{
						return false; 
					}
					if (has_vert_color)
					{
						C_rect = igl::list_to_matrix(cSet, C_subset);
						if (!C_rect)
						{
							return false;
						}
					}
					
					//TODO: Filling hole here

					if (has_vert_color)
					{
						if (igl::writeOFF(std::string("") + suGlobalState::gOnly().object_labels[iLabel] + std::string(".off"), V_subset, F_subset, C_subset))
						{
							std::cout << suGlobalState::gOnly().object_labels[iLabel] + std::string(".off") << " is generated.\n";
						}
					}
					else
					{
						if (igl::writeOFF(std::string("") + suGlobalState::gOnly().object_labels[iLabel] + std::string(".off"), V_subset, F_subset))
						{
							std::cout << suGlobalState::gOnly().object_labels[iLabel] + std::string(".off") << " is generated.\n";
						}
					}
					

				}
				//std::vector<std::vector<Eigen::DenseIndex>> &Fi = Fs[0];
				//std::cout << Fi.size() << std::endl;
				return true;
			}


		}

	}
}