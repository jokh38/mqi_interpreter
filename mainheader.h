#pragma once
#define STB_IMAGE_IMPLEMENTATION
#define NOMINMAX

#include <iostream> // input and output stream
#include <filesystem> // standard filesystem
#include <fstream> // standard file stream
#include <thread> // for multi-threading
#include <cmath> // standard math library
#include <WinSock2.h> // to use Little endian to Big endian
#include <math.h>

#include "imebra/imebra.h" // DICOM c++ library

// Xtensor library (numpy like)
#include "xtensor/xarray.hpp"
#include "xtensor/xio.hpp"
#include "xtensor/xview.hpp"
#include "xtensor/xadapt.hpp" // to print out with standard output

// Graphic library
#include "GL/gl3w.h" // gl3w
#include "GLFW/glfw3.h" // glfw

// GUI library (ImGui, Immediate Mode GUI)
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
#include "ImGuiFileDialog.h"
#include "implot.h"
#include "implot_internal.h"

#include "boost/math/interpolators/pchip.hpp" // for beam spot interpolation
#include "libInterpolate/Interpolate.hpp"// for dipole magnet tesla interpolation
#include "stb_image.h" // Image load library
#include "OpenXLSX.hpp" // xlsx file format load library

// Font
// basic font size = 16.0f
// middle font size = 20.0f
// big font size = 25.0f
ImFont* basicFont;
ImFont* bigFont;
ImFont* middleFont;
ImFont* smallFont;

// MOQUI related variables
struct moquiPhantomProperty
{
	int x;
	int y;
	int z;
};

bool MOQUICodeGenerating{};
bool MOQUICodeGenerateStarted{};
bool MOQUICodeGenerated{};
float MOQUICodeGenerationProgress{ 0.0f };

// For CT option
bool useHUtoMaterialSchneider{ false };

// For calibration option
bool setForCalibration{ false };
bool useCorrectionFactorForCalibration{ true };
bool calibModeMultiEnergyLayer{ false };

// Particle count result releated variable
std::vector<std::vector<float>>particleCountResult;

// Show extra function in menu related variable
bool showPtnRawValue{ false };
bool showMgnRawValue{ false };
bool showMgnValueAsScatter{ false };
bool showMgnValueAsLineAndScatter{ false };
bool savePtnAsExcel{ false };
bool saveMgnAsExcel{ false };
bool showLogDivWindow{ false };

// RT plan related variable
bool RTPlanLoading{ false };
bool RTPlanFileLoaded{ false };
bool modalityErrorFlag{ false };

ImGuiFileDialog RTPlanDialog;
std::string modality{};
std::string RTPlanfileName{};
std::string RTPlanfileFolderPath{};
std::string RTplanfileFullPath{};
std::string RTPlanPatientID{};
std::string RTPlanDate{};
std::string RTPlanName{};
std::string RTPlanBeamEnergyUnit{};
std::vector<std::string> RTPlanBeamNameList;
std::vector<std::string> RTPlanDegraderList;
std::vector<float> RTPlanEnergyLayerTemp;
std::vector<float> RTPlanEnergyLayerMetersetTemp;
std::vector<float> RTPlanSnoutPosition;
std::vector<std::vector<float>> RTPlanEnergyLayer;
std::vector<std::vector<float>> RTPlanEnergyLayerMeterset;
int RTPlanNumberOfBeams{};

// Log file related variable
bool ptnOnlyMode{ false }; // use ptn only if checked
bool ActConPtnOnlyMode{ false };
bool logFileLoading{ false };
bool logFileLoaded{ false };
bool logFileNotIncluded{ false };
bool logFileNotMatch{ false };

ImGuiFileDialog logDialog;
std::string logFileFullPath{};
std::string logFileFolderPath{};
std::vector<std::string> mgnFilePathList;
std::vector<std::string> ptnFilePathList;
std::vector<std::string> mgnFileNameList;
std::vector<std::string> ptnFileNameList;
std::vector<xt::xarray<float>> mgnDataSet;
std::vector<xt::xarray<float>> ptnDataSet;
std::vector<std::vector<double>> XTeslaDataset;
std::vector<std::vector<double>> YTeslaDataset;

int doseDividingFactor{ 10 };

// Log file MGN & PTN graph releated bool variable
int ptnSelected{ -1 };
int ptnDataContainerSize{};
int mgnDataContainerSize{};
int logFilePositionRange{ 150 };
bool ptnSelectChanged{ false };
bool ptnSelectChangedTime{ false };
bool showPtnIntensity{ false };
bool showPtnTimePosition{ false };
std::vector<float> ptnXDataVector;
std::vector<float> ptnYDataVector;
std::vector<float> mgnXDataVector;
std::vector<float> mgnYDataVector;
std::vector<float> mgnXDataPlotVector;
std::vector<float> mgnYDataPlotVector;
std::vector<float> ptnTimeDataVector;
std::vector<float> ptnDoseMonitorDataVector;
float ptnDoseMonitorMax{ 0 };
std::vector<float> mgnTimeDataVector;

// Log file interpretation related variable
float XPRESETOFFSET{};
float YPRESETOFFSET{};
float XPRESETGAIN{};
float YPRESETGAIN{};
float TIMEGAIN{};
float XPOSOFFSET{};
float YPOSOFFSET{};
float XPOSGAIN{};
float YPOSGAIN{};

// Dose monitor range setting related variable
ImGuiFileDialog doseMonitorRangeDialog;
bool doseMonitorRangeManualSettingWindow{ false };
bool doseMonitorRangeFileSettingWindow{ false };
bool doseMonitorSettingDone{ false };
bool doseMonitorRangeFileLoading{ false };
bool doseMonitorRangeFileLengthNotFit{ false };
std::vector<int> currentLogMonitorRange;
std::string doseMonitorRangeFileFullPath{};
std::string doseMonitorRangeFileFolderPath{};

// Log file info save related variable
bool logFileExcelSaving{ false };
bool logFileDivSaving{ false };

// TOPAS code generation related variable
bool TOPASCodeGenerateStarted{ false };
bool TOPASCodeGenerating{ false };
bool TOPASCodeGenerated{ false };

bool TOPASBaseCodeNotExist{ false };
float TOPASCodeGenerationProgress{ 0.0f };
bool folderAlreadyExists{ false };

// Thread function declaration
void doseMonitorRangeFileThread();
void RTPlanLoadingThread();
void logFileLoadingThread();
void TOPASThread();
void logFileExcelSaveThread();
void logFileDivSaveThread();
void MOQUIThread();

// Image loading helper function
bool LoadTextureFromFile(const char* filename, GLuint* out_texture, int* out_width, int* out_height)
{
	// Load from file
	int image_width = 0;
	int image_height = 0;
	unsigned char* image_data = stbi_load(filename, &image_width, &image_height, NULL, 4);
	if (image_data == NULL)
		return false;

	// Create a OpenGL texture identifier
	GLuint image_texture;
	glGenTextures(1, &image_texture);
	glBindTexture(GL_TEXTURE_2D, image_texture);

	// Setup filtering parameters for display
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE); // This is required on WebGL for non power-of-two textures
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE); // Same

	// Upload pixels into texture
#if defined(GL_UNPACK_ROW_LENGTH) && !defined(__EMSCRIPTEN__)
	glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
#endif
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data);
	stbi_image_free(image_data);

	*out_texture = image_texture;
	*out_width = image_width;
	*out_height = image_height;

	return true;
}

// ImGui toggle button function
void ToggleButton(const char* str_id, bool* v)
{
	ImVec2 p = ImGui::GetCursorScreenPos();
	ImDrawList* draw_list = ImGui::GetWindowDrawList();

	float height = ImGui::GetFrameHeight();
	float width = height * 1.55f;
	float radius = height * 0.50f;

	ImGui::InvisibleButton(str_id, ImVec2(width, height));
	if (ImGui::IsItemClicked())
		*v = !*v;

	float t = *v ? 1.0f : 0.0f;

	ImGuiContext& g = *GImGui;
	float ANIM_SPEED = 0.08f;
	if (g.LastActiveId == g.CurrentWindow->GetID(str_id))// && g.LastActiveIdTimer < ANIM_SPEED)
	{
		float t_anim = ImSaturate(g.LastActiveIdTimer / ANIM_SPEED);
		t = *v ? (t_anim) : (1.0f - t_anim);
	}

	ImU32 col_bg;
	if (ImGui::IsItemHovered())
		col_bg = ImGui::GetColorU32(ImLerp(ImVec4(0.78f, 0.78f, 0.78f, 1.0f), ImVec4(0.64f, 0.83f, 0.34f, 1.0f), t));
	else
		col_bg = ImGui::GetColorU32(ImLerp(ImVec4(0.85f, 0.85f, 0.85f, 1.0f), ImVec4(0.56f, 0.83f, 0.26f, 1.0f), t));

	draw_list->AddRectFilled(p, ImVec2(p.x + width, p.y + height), col_bg, height * 0.5f);
	draw_list->AddCircleFilled(ImVec2(p.x + radius + t * (width - radius * 2.0f), p.y + radius), radius - 1.5f, IM_COL32(255, 255, 255, 255));
}

// Loading ImGui menu
void getMenu()
{
	/* Pre-setting for bool varaibles */
	if (logFileLoaded)
	{
		if (mgnDataSet.size() > 0) ActConPtnOnlyMode = true;
		else ActConPtnOnlyMode = false;
	}
	else ActConPtnOnlyMode = true;

	if (ptnOnlyMode) 
	{
		showMgnRawValue = false; 
		showLogDivWindow = false;
	}

	/* Pre-setting for bool varaibles */

	if (ImGui::BeginMainMenuBar())
	{
		if (ImGui::BeginMenu("Calibration"))
		{
			ImGui::MenuItem("Use correction factor", "(It is effective when calibration mode is on.)", &useCorrectionFactorForCalibration, setForCalibration);
			ImGui::MenuItem("Use multi-layer information", "(This option distinguish previous same energy layer)", &calibModeMultiEnergyLayer, setForCalibration);
			ImGui::MenuItem("Calibration mode", "(Use for handling customized RT plan file)", &setForCalibration, true);
			
			ImGui::EndMenu();
		}

		if (ImGui::BeginMenu("Log file"))
		{
			ImGui::MenuItem("Show .ptn value view window", "(This window shows selected ptn file information.)", &showPtnRawValue, true);
			ImGui::MenuItem("Show .mgn value view window", "(This window shows mgn file information matched with selected ptn file.)", &showMgnRawValue, !ptnOnlyMode);
			if (ImGui::MenuItem("Use .ptn file only", " (If this option is on, you don't need to ready mgn file. Disabled to check off if you have only ptn dataset) ", &ptnOnlyMode, ActConPtnOnlyMode))
			{
				if (logFileLoaded)
				{
					ptnSelectChanged = true;
					if (showPtnTimePosition) ptnSelectChangedTime = true;
				}
			}
			ImGui::MenuItem("Show log file division window", "Divide log information to line segment unit. Disabled in ptn only mode.", &showLogDivWindow, !ptnOnlyMode);
			ImGui::EndMenu();
		}

		if (ImGui::BeginMenu("Graph"))
		{
			if (ImGui::MenuItem("Show .mgn value as scatter", "(Basically, the graph shows information as line.)", &showMgnValueAsScatter, true))
			{
				if (showMgnValueAsLineAndScatter) showMgnValueAsLineAndScatter = false;
			}
			if (ImGui::MenuItem("Show .mgn value as Line and Scatter", "(Basically, the graph shows information as line.)", &showMgnValueAsLineAndScatter, true))
			{
				if (showMgnValueAsScatter) showMgnValueAsScatter = false;
			}
			ImGui::EndMenu();
		}

		if (ImGui::BeginMenu("Extra"))
		{
			ImGui::MenuItem("Use Schneider", "Use HU to material function for CT calculation", &useHUtoMaterialSchneider, true);
			ImGui::EndMenu();
		}

		ImGui::EndMainMenuBar();
	}
}

// Logo and auther information
void getLogoAndAuthor(GLuint* logo_texture, int* logo_width, int* logo_height)
{
	// Logo texture to ImGui::Image
	ImGui::SetNextWindowPos(ImVec2(1, 25));
	ImGui::SetNextWindowSize(ImVec2(float(*logo_width + 500), float(*logo_height + 15)));
	ImGui::Begin("Logo", NULL, ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
	ImGui::Image((void*)(intptr_t)*logo_texture, ImVec2(float(*logo_width), float(*logo_height)));
	ImGui::SameLine();
	ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 5);
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 15);
	ImGui::Text("Log file based MC code generator for pQA (Ver 2.0.1, 2024-05-09)");
	ImGui::End();

	// Acknowledgment
	ImGui::SetNextWindowPos(ImVec2(10, 865));
	ImGui::SetNextWindowSize(ImVec2(1225, 20));
	ImGui::Begin("Acknowledgement", NULL, ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground);
	ImGui::SetCursorPosX((ImGui::GetWindowSize().x - ImGui::CalcTextSize("Acknowledgment : Thank Jaehyeon Seo for contribution about log file interpretation / Chanil Jeon's Email : potential_ee@naver.com").x) / 2);
	ImGui::Text("Acknowledgment : Thank Jaehyeon Seo for contribution to log file interpretation / Chanil Jeon's Email : potential_ee@naver.com");
	ImGui::End();
}

// Rendering default widget
void getDefaultWidget()
{
	// ### 1. Log file information window ###

	ImGui::SetNextWindowPos(ImVec2(10, 80), ImGuiCond_Always);
	ImGui::SetNextWindowSize(ImVec2(610, 780));
	ImGui::Begin("Log file window", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_HorizontalScrollbar);

	// File dialog display button
	// Button rounding style start
	ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);
	if (ImGui::Button("Load log files (Choose a log file in the log file directory)"))
	{
		if (logFileLoaded == false && logFileLoading == false)
		{
			logDialog.SetExtentionInfos(".ptn", ImVec4(0, 0, 1, 1.0));
			logDialog.SetExtentionInfos(".mgn", ImVec4(0, 0, 1, 1.0));
			logDialog.OpenDialog("ChooseLogFile", "Choose a log file", ".ptn,.mgn", " ");
		}
		else if (logFileLoaded == true && logFileLoading == false) ImGui::OpenPopup("log-file-already-loaded-error");
		else if (logFileLoaded == false && logFileLoading == true) ImGui::OpenPopup("log-file-now-loading-error");
	}

	// File dialog display
	if (logDialog.Display("ChooseLogFile", ImGuiWindowFlags_NoCollapse, ImVec2(700, 300)))
	{
		if (logDialog.IsOk())
		{
			logFileFullPath = logDialog.GetFilePathName();
			logFileFolderPath = logDialog.GetCurrentPath();

			std::filesystem::path p(logFileFullPath);

			if (std::filesystem::exists(p) == false) ImGui::OpenPopup("not-valid-log-file-path-error");
			else
			{
				logFileLoading = true;
				std::thread thread(logFileLoadingThread);
				thread.detach();
			}
		}
		logDialog.Close();
	}

	/* Error handling (popup) */
	// If log file path is not vaild, show error
	if (ImGui::BeginPopupModal("not-valid-log-file-path-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("The path is not valid.\nPlease choose right path from file dialog.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 70);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If log file is already loaded, show error
	if (ImGui::BeginPopupModal("log-file-already-loaded-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 80);
		ImGui::Text("Log files are already loaded.");
		ImGui::Text("Please intialize status before loading new log files.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If log file is now loading, show error
	if (ImGui::BeginPopupModal("log-file-now-loading-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Log files are now being loaded.\nPlease wait until full load.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If log file path has no log file, show error
	if (logFileNotIncluded == true)
	{
		ImGui::OpenPopup("no-proper-log-file-in-folder-error");
		logFileNotIncluded = false;
	}

	if (ImGui::BeginPopupModal("no-proper-log-file-in-folder-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("The path don't have proper log file set.\nPlease make right mgn-ptn set and choose a log file.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If log files are not matched, show error
	if (logFileNotMatch == true)
	{
		ImGui::OpenPopup("not-files-not-match-error");
		logFileNotMatch = false;
	}

	if (ImGui::BeginPopupModal("not-files-not-match-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text(".mgn and .ptn log file count is not matched.\n.Please check .mgn and .ptn count is same.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	ImGui::SameLine();

	// Log file loading status initializing button
	if (ImGui::Button("Initialize load status"))
	{
		particleCountResult.clear();
		currentLogMonitorRange.clear();

		mgnFilePathList.clear();
		ptnFilePathList.clear();
		mgnFileNameList.clear();
		ptnFileNameList.clear();

		mgnDataSet.clear();
		ptnDataSet.clear();
		XTeslaDataset.clear();
		YTeslaDataset.clear();

		ptnXDataVector.clear();
		ptnYDataVector.clear();
		mgnXDataVector.clear();
		mgnYDataVector.clear();

		ptnSelected = -1;
		doseMonitorRangeManualSettingWindow = false;
		doseMonitorRangeFileSettingWindow = false;
		doseMonitorSettingDone = false;
		logFileLoaded = false;
	}

	// Button rounding style end
	ImGui::PopStyleVar();

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 3);

	if (logFileLoaded == false && logFileLoading == false)
	{
		ImGui::Text("Log file folder path : Not loaded");

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("Logfilelist", ImVec2(585, 250), true, ImGuiWindowFlags_None);
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 100);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
		ImGui::PushFont(bigFont);
		ImGui::Text("Log file not loaded");
		ImGui::PopFont();
		ImGui::EndChild();
		ImGui::PopStyleVar();
	}
	else if (logFileLoaded == false && logFileLoading == true)
	{
		ImGui::Text("Log file folder path : Not loaded");

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("Logfilelist", ImVec2(585, 250), true, ImGuiWindowFlags_None);
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 90);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 170);
		ImGui::PushFont(bigFont);
		ImGui::Text("Log file is being loaded");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 220);
		ImGui::Text("Please wait..");
		ImGui::PopFont();
		ImGui::EndChild();
		ImGui::PopStyleVar();
	}
	else if (logFileLoaded == true)
	{
		ImGui::Text("Log file folder path : %s", logFileFolderPath.c_str());

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("Logfilelist", ImVec2(585, 250), true, ImGuiWindowFlags_None);
		for (int i = 0; i < ptnFileNameList.size(); i++)
		{
			if (ImGui::Selectable(ptnFileNameList[i].c_str(), ptnSelected == i))
			{
				ptnSelected = i;
				ptnSelectChanged = true;
				ptnSelectChangedTime = true;
			}
		}
		ImGui::EndChild();
		ImGui::PopStyleVar();
	}

	// Log file spot size half slider
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 7);
	ImGui::PushItemWidth(180);
	ImGui::PushID("SpotSizeHalf");
	ImGui::SliderInt(" ", &logFilePositionRange, 10, 300, "Spot size half : %d mm");
	ImGui::PopID();
	ImGui::SameLine();

	// Log file information by time and X,Y
	ImGui::Text("Time / X-Y-Dose");
	ImGui::SameLine();
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 1);
	ToggleButton("ptnTimePositionButton", &showPtnTimePosition);
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() - 1);

	// Log file graph intensity information toggle button
	ImGui::SameLine();
	ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 5);
	ImGui::Text("PTN dose distribution weight");
	ImGui::SameLine();
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 1);
	ToggleButton("ptnGraphToggleButton", &showPtnIntensity);
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() - 1);
	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

	// If log file not loaded, just show the basic plot
	if (logFileLoaded == false)
	{
		ImGui::PushFont(smallFont);
		ImPlot::CreateContext();
		static double xData[11], yData[11];
		if (ImPlot::BeginPlot("Log file pattern data", "X", "Y", ImVec2(585, 385), ImPlotFlags_NoMenus)) {
			ImPlot::PlotLine("", xData, yData, 11);
			ImPlot::EndPlot();
		}
		ImPlot::DestroyContext();
		ImGui::PopFont();
	}
	else
	{
		if (ptnSelectChanged == true)
		{
			ptnXDataVector.clear();
			ptnYDataVector.clear();
			mgnXDataVector.clear();
			mgnYDataVector.clear();

			// PTN position data extract
			auto ptnPositionXView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(1, 2));
			auto ptnPositionYView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(2, 3));
			xt::xarray<float> ptnPositionXArray(ptnPositionXView);
			xt::xarray<float> ptnPositionYArray(ptnPositionYView);
			std::vector<float> ptnXDataContainer(ptnPositionXArray.begin(), ptnPositionXArray.end());
			std::vector<float> ptnYDataContainer(ptnPositionYArray.begin(), ptnPositionYArray.end());
			ptnDataContainerSize = int(ptnXDataContainer.size());
			ptnXDataVector.resize(ptnDataContainerSize);
			ptnYDataVector.resize(ptnDataContainerSize);
			std::copy(ptnXDataContainer.begin(), ptnXDataContainer.end(), ptnXDataVector.begin());
			std::copy(ptnYDataContainer.begin(), ptnYDataContainer.end(), ptnYDataVector.begin());

			if (!ptnOnlyMode)
			{
				// MGN position data extract
				auto mgnPositionXView = xt::view(mgnDataSet[ptnSelected], xt::all(), xt::range(3, 4));
				auto mgnPositionYView = xt::view(mgnDataSet[ptnSelected], xt::all(), xt::range(4, 5));
				xt::xarray<float> mgnPositionXArray(mgnPositionXView);
				xt::xarray<float> mgnPositionYArray(mgnPositionYView);
				std::vector<float> mgnXDataContainer(mgnPositionXArray.begin(), mgnPositionXArray.end());
				std::vector<float> mgnYDataContainer(mgnPositionYArray.begin(), mgnPositionYArray.end());
				mgnDataContainerSize = int(mgnXDataContainer.size());
				mgnXDataVector.resize(mgnDataContainerSize);
				mgnYDataVector.resize(mgnDataContainerSize);
				std::copy(mgnXDataContainer.begin(), mgnXDataContainer.end(), mgnXDataVector.begin());
				std::copy(mgnYDataContainer.begin(), mgnYDataContainer.end(), mgnYDataVector.begin());
				mgnXDataContainer.pop_back();
				mgnYDataContainer.pop_back();
				mgnXDataContainer.erase(mgnXDataContainer.begin());
				mgnYDataContainer.erase(mgnYDataContainer.begin());
				mgnXDataPlotVector.resize(mgnDataContainerSize - 2);
				mgnYDataPlotVector.resize(mgnDataContainerSize - 2);
				std::copy(mgnXDataContainer.begin(), mgnXDataContainer.end(), mgnXDataPlotVector.begin());
				std::copy(mgnYDataContainer.begin(), mgnYDataContainer.end(), mgnYDataPlotVector.begin());
			}

			ptnSelectChanged = false;
		}

		if (ptnSelected != -1)
		{
			ImGui::PushFont(smallFont);
			ImPlot::CreateContext();

			ImPlot::SetNextPlotLimits(-(logFilePositionRange), logFilePositionRange, -logFilePositionRange, logFilePositionRange);

			if (ImPlot::BeginPlot("Log file pattern data", "X (mm)", "Y (mm)", ImVec2(585, 385), ImPlotFlags_NoMenus)) {
				if (showPtnIntensity == true) ImPlot::SetNextMarkerStyle(ImPlotMarker_Circle, 2.5f, ImVec4(0, 0, 1.f, 1.f), IMPLOT_AUTO);
				ImPlot::PlotScatter("Actual", ptnXDataVector.data(), ptnYDataVector.data(), ptnDataContainerSize);
				ImPlot::SetNextLineStyle(ImVec4(1.f, 0.f, 0.0f, 1.f), 2.0f);
				if (!ptnOnlyMode)
				{
					if (showMgnValueAsScatter) ImPlot::PlotScatter("Plan", mgnXDataVector.data(), mgnYDataVector.data(), mgnDataContainerSize);
					else if (showMgnValueAsLineAndScatter)
					{
						ImPlot::SetNextMarkerStyle(ImPlotMarker_Circle);
						ImPlot::PlotLine("Plan", mgnXDataPlotVector.data(), mgnYDataPlotVector.data(), mgnDataContainerSize - 2);
					}
					else ImPlot::PlotLine("Plan", mgnXDataPlotVector.data(), mgnYDataPlotVector.data(), mgnDataContainerSize - 2);
				}
				ImPlot::EndPlot();
			}

			ImPlot::DestroyContext();
			ImGui::PopFont();
		}
		else
		{
			ImGui::PushFont(smallFont);
			ImPlot::CreateContext();
			static double xData[11], yData[11];
			if (ImPlot::BeginPlot("Log file pattern data", "X", "Y", ImVec2(585, 385), ImPlotFlags_NoMenus)) {
				ImPlot::PlotLine("", xData, yData, 11);
				ImPlot::EndPlot();
			}
			ImPlot::DestroyContext();
			ImGui::PopFont();
		}
	}

	ImGui::End();

	// ### 1-1. Log file time / X-Y-Dose Info
	if (logFileLoaded == true)
	{
		// If select button pushed, loading the plot data
		if (ptnSelectChangedTime == true)
		{
			if (ptnOnlyMode)
			{
				ptnTimeDataVector.clear();
				ptnDoseMonitorDataVector.clear();

				// PTN position data extract
				auto ptnTimeView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(0, 1));
				auto ptnDoseMonitorView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(5, 6));

				xt::xarray<float> ptnTimeArray(ptnTimeView);
				xt::xarray<float> ptnDoseMonitorArray(ptnDoseMonitorView);

				std::vector<float> ptnTimeDataContainer(ptnTimeArray.begin(), ptnTimeArray.end());
				std::vector<float> ptnDoseMonitorDataContainer(ptnDoseMonitorArray.begin(), ptnDoseMonitorArray.end());

				ptnTimeDataVector.resize(ptnDataContainerSize);
				ptnDoseMonitorDataVector.resize(ptnDataContainerSize);

				std::copy(ptnTimeDataContainer.begin(), ptnTimeDataContainer.end(), ptnTimeDataVector.begin());
				std::copy(ptnDoseMonitorDataContainer.begin(), ptnDoseMonitorDataContainer.end(), ptnDoseMonitorDataVector.begin());

				ptnDoseMonitorMax = *(std::max_element)(ptnDoseMonitorDataVector.begin(), ptnDoseMonitorDataVector.end());
			}
			else
			{
				ptnTimeDataVector.clear();
				mgnTimeDataVector.clear();
				ptnDoseMonitorDataVector.clear();

				// PTN position data extract
				auto ptnTimeView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(0, 1));
				auto mgnTimeView = xt::view(mgnDataSet[ptnSelected], xt::all(), xt::range(0, 1));
				auto ptnDoseMonitorView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(5, 6));

				xt::xarray<float> ptnTimeArray(ptnTimeView);
				xt::xarray<float> mgnTimeArray(mgnTimeView);
				xt::xarray<float> ptnDoseMonitorArray(ptnDoseMonitorView);

				std::vector<float> ptnTimeDataContainer(ptnTimeArray.begin(), ptnTimeArray.end());
				std::vector<float> mgnTimeDataContainer(mgnTimeArray.begin(), mgnTimeArray.end());
				std::vector<float> ptnDoseMonitorDataContainer(ptnDoseMonitorArray.begin(), ptnDoseMonitorArray.end());

				// Convert us to ms
				for (int i = 0; i < mgnTimeDataContainer.size(); i++) mgnTimeDataContainer[i] = mgnTimeDataContainer[i] / 1000;

				ptnTimeDataVector.resize(ptnDataContainerSize);
				mgnTimeDataVector.resize(mgnDataContainerSize);
				ptnDoseMonitorDataVector.resize(ptnDataContainerSize);

				std::copy(ptnTimeDataContainer.begin(), ptnTimeDataContainer.end(), ptnTimeDataVector.begin());
				std::copy(mgnTimeDataContainer.begin(), mgnTimeDataContainer.end(), mgnTimeDataVector.begin());
				std::copy(ptnDoseMonitorDataContainer.begin(), ptnDoseMonitorDataContainer.end(), ptnDoseMonitorDataVector.begin());

				ptnDoseMonitorMax = *(std::max_element)(ptnDoseMonitorDataVector.begin(), ptnDoseMonitorDataVector.end());
			}
			

			ptnSelectChangedTime = false;
		}

		if (showPtnTimePosition == true)
		{
			ImGui::SetNextWindowPos(ImVec2(625, 32), ImGuiCond_Always);
			ImGui::SetNextWindowSize(ImVec2(610, 818));
			ImGui::Begin(" Log file time-position info", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoScrollWithMouse);

			// If selected state, show the plot
			if (ptnSelected != -1)
			{
				ImGui::PushFont(smallFont);
				ImPlot::CreateContext();
				ImPlot::SetNextPlotLimits(0, ptnTimeDataVector.back(), -logFilePositionRange, logFilePositionRange);
				if (ImPlot::BeginPlot("Time / X poisition data", "Time (ms)", "X (mm)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::SetNextLineStyle(ImVec4(0.f, 0.f, 1.f, 1.f), 5);
					ImPlot::PlotLine("Actual", ptnTimeDataVector.data(), ptnXDataVector.data(), ptnDataContainerSize);
					ImPlot::SetNextLineStyle(ImVec4(1.f, 0.f, 0.f, 1.f), 2);
					if (!ptnOnlyMode)
					{
						if (!showMgnValueAsScatter) ImPlot::PlotLine("Plan", mgnTimeDataVector.data(), mgnXDataVector.data(), mgnDataContainerSize);
						else ImPlot::PlotScatter("Plan", mgnTimeDataVector.data(), mgnXDataVector.data(), mgnDataContainerSize);
					}
						
					ImPlot::EndPlot();
				}

				ImPlot::SetNextPlotLimits(0, ptnTimeDataVector.back(), -logFilePositionRange, logFilePositionRange);
				if (ImPlot::BeginPlot("Time / Y poisition data", "Time (ms)", "Y (mm)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::SetNextLineStyle(ImVec4(0.f, 0.f, 1.f, 1.f), 5);
					ImPlot::PlotLine("Actual", ptnTimeDataVector.data(), ptnYDataVector.data(), ptnDataContainerSize);
					ImPlot::SetNextLineStyle(ImVec4(1.f, 0.f, 0.f, 1.f), 2);
					if (!ptnOnlyMode)
					{
						if (!showMgnValueAsScatter) ImPlot::PlotLine("Plan", mgnTimeDataVector.data(), mgnYDataVector.data(), mgnDataContainerSize);
						else  ImPlot::PlotScatter("Plan", mgnTimeDataVector.data(), mgnYDataVector.data(), mgnDataContainerSize);
					}
						
					ImPlot::EndPlot();
				}
				ImPlot::SetNextPlotLimits(0, ptnTimeDataVector.back(), 0, ptnDoseMonitorMax + 2000);
				if (ImPlot::BeginPlot("Time / Dose monitor data", "Time (ms)", "Dose (a.u.)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::SetNextLineStyle(ImVec4(0.f, 0.f, 1.f, 1.f), 2);
					ImPlot::PlotLine("Actual", ptnTimeDataVector.data(), ptnDoseMonitorDataVector.data(), ptnDataContainerSize);
					ImPlot::EndPlot();
				}
				ImPlot::DestroyContext();
				ImGui::PopFont();
			}
			else
			{
				ImGui::PushFont(smallFont);
				ImPlot::CreateContext();
				static double timeData[11], xData[11], yData[11], doseData[11];
				if (ImPlot::BeginPlot("Time and X poisition data", "Time (ms)", "X (mm)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::PlotLine("", timeData, xData, 11);
					ImPlot::EndPlot();
				}
				if (ImPlot::BeginPlot("Time and Y poisition data", "Time (ms)", "Y (mm)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::PlotLine("", timeData, yData, 11);
					ImPlot::EndPlot();
				}
				if (ImPlot::BeginPlot("Time / Dose monitor data", "Time (ms)", "Dose (a.u.)", ImVec2(590, 263), ImPlotFlags_NoMenus)) {
					ImPlot::PlotLine("", timeData, doseData, 11);
					ImPlot::EndPlot();
				}
				ImPlot::DestroyContext();
				ImGui::PopFont();
			}

			ImGui::End();
		}
	}
	
	// ### 2. RT plan lnformation window ###

	ImGui::SetNextWindowPos(ImVec2(625, 280), ImGuiCond_Always);
	ImGui::SetNextWindowSize(ImVec2(610, 580));
	ImGui::Begin(" RT plan window", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_HorizontalScrollbar);

	// DICOM RT Plan load button
	// Button rounding style start
	ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);
	if (ImGui::Button("Load DICOM RT plan file"))
	{
		if (RTPlanFileLoaded == false && RTPlanLoading == false)
		{
			RTPlanDialog.SetExtentionInfos(".dcm", ImVec4(0, 0, 1, 1.0));
			RTPlanDialog.OpenDialog("ChooseRTPlanFile", "Choose RT plan file", ".dcm", "");
		}
		else if (RTPlanFileLoaded == false && RTPlanLoading == true) ImGui::OpenPopup("RT-plan-now-loading-error");
		else if (RTPlanFileLoaded == true) ImGui::OpenPopup("RT-plan-already-loaded-error");
	}

	if (RTPlanDialog.Display("ChooseRTPlanFile", ImGuiWindowFlags_NoCollapse, ImVec2(700, 300)))
	{
		if (RTPlanDialog.IsOk())
		{
			RTplanfileFullPath = RTPlanDialog.GetFilePathName();
			RTPlanfileName = RTPlanDialog.GetCurrentFileName();
			RTPlanfileFolderPath = RTPlanDialog.GetCurrentPath();

			std::filesystem::path p(RTplanfileFullPath);

			if (std::filesystem::exists(p) == false) ImGui::OpenPopup("not-valid-RTplan-path-error");
			else
			{
				RTPlanLoading = true;
				std::thread thread(RTPlanLoadingThread);
				thread.detach();
			}
		}
		RTPlanDialog.Close();
	}

	ImGui::SameLine();

	// RT plan loading status initializing button
	if (ImGui::Button("Initialize load status"))
	{
		RTPlanBeamNameList.clear();
		RTPlanEnergyLayer.clear();
		RTPlanSnoutPosition.clear();
		RTPlanDegraderList.clear();
		RTPlanEnergyLayerMeterset.clear();
		particleCountResult.clear();

		doseMonitorRangeManualSettingWindow = false;
		doseMonitorRangeFileSettingWindow = false;
		doseMonitorSettingDone = false;
		RTPlanFileLoaded = false;
	}

	/* Error handling (popup) */

	// If RTPlan file path is not vaild, show error
	if (ImGui::BeginPopupModal("not-valid-RTplan-path-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("The path is not valid.\nPlease choose right path from file dialog.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// RT plan already loaded error popup
	if (ImGui::BeginPopupModal("RT-plan-already-loaded-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 120);
		ImGui::Text("RT plan is already loaded.");
		ImGui::Text("Please initialize loading status before loading another RT plan.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 140);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// RT plan now loading error popup
	if (ImGui::BeginPopupModal("RT-plan-now-loading-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 80);
		ImGui::Text("RT plan is now being loaded.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 80);
		ImGui::Text("Please wait until full load.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If dicom modality is not RTPLAN, show the error popup
	if (logFileLoading == false && modalityErrorFlag == true)
	{
		ImGui::OpenPopup("is-not-RTplan-error");
		modalityErrorFlag = false;
	}

	// If Modality is not RTPLAN, show error
	if (ImGui::BeginPopupModal("is-not-RTplan-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("This DICOM file is not RTPLAN.\nPlease choose DICOM RT plan file.\n");

		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 50);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// Button rounding style end
	ImGui::PopStyleVar();

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

	ImGui::TextColored(ImVec4(0, 0, 1, 1), "# RT Plan information #");

	// 1. RT plan not loaded, 2. RT plan loading, 3. RT plan loaded 
	if (RTPlanFileLoaded == false)
	{
		if (RTPlanLoading == false)
		{
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("RT-plan-before-load", ImVec2(593, 470), true);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 200);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("RT plan not loaded");
			ImGui::PopFont();
			ImGui::EndChild();
			ImGui::PopStyleVar();
		}
		else if (RTPlanLoading == true)
		{
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("RT-plan-after-load", ImVec2(593, 470), true);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 190);
			ImGui::PushFont(bigFont);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 130);
			ImGui::Text("Program is now loading RT plan");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 220);
			ImGui::Text("Please wait..");
			ImGui::PopFont();
			ImGui::EndChild();
			ImGui::PopStyleVar();
		}

	}
	else if (RTPlanFileLoaded == true)
	{
		// Show the rt plan information

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::Text("File name : %s", RTPlanfileName.c_str());
		ImGui::Text("File Location : %s", RTPlanfileFolderPath.c_str());

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::Text("Patient ID : %s", RTPlanPatientID.c_str());
		ImGui::Text("RT Plan date : %s", RTPlanDate.c_str());
		ImGui::Text("RT Plan name : %s", RTPlanName.c_str());

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::Text("Number of beams : %d", RTPlanNumberOfBeams);

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("RTPlan Info Child", ImVec2(594, 315), true);
		ImGui::PopStyleVar();

		ImDrawList* draw_list = ImGui::GetWindowDrawList();

		for (int i = 0; i < RTPlanNumberOfBeams; i++)
		{
			draw_list->AddLine(ImVec2(ImGui::GetCursorScreenPos().x, ImGui::GetCursorScreenPos().y), ImVec2(ImGui::GetCursorScreenPos().x + 585, ImGui::GetCursorScreenPos().y), ImColor(ImVec4(0.f, 0.f, 0.f, 1.f)), 3.0f);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 7);
			ImGui::Text("Beam %d (%s, %s)", i + 1, RTPlanBeamNameList[i].c_str(), RTPlanDegraderList[i].c_str());
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);
			draw_list->AddLine(ImVec2(ImGui::GetCursorScreenPos().x, ImGui::GetCursorScreenPos().y), ImVec2(ImGui::GetCursorScreenPos().x + 585, ImGui::GetCursorScreenPos().y), ImColor(ImVec4(0.f, 0.f, 0.f, 1.f)), 3.0f);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 7);
			ImGui::Text("Number of energy layer : %d ,", RTPlanEnergyLayer[i].size());
			ImGui::SameLine();
			ImGui::Text("Energy range : %0.1f - %0.1f (%s)", RTPlanEnergyLayer[i].back(), RTPlanEnergyLayer[i].front(), RTPlanBeamEnergyUnit.c_str());
			
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);
			
			ImGui::Text("Energy layer :");
			ImGui::SameLine();
			for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
			{
				if (j == RTPlanEnergyLayer[i].size() - 1)
				{
					ImGui::Text("%0.1f", RTPlanEnergyLayer[i][j]);
					ImGui::SameLine();
				}	
				else if (j == 9 || j == 21 || j == 33 || j == 45 || j == 57 || j == 69 || j == 81)
				{
					ImGui::Text("%0.1f,", RTPlanEnergyLayer[i][j]);
				}
				else
				{
					ImGui::Text("%0.1f,", RTPlanEnergyLayer[i][j]);
					ImGui::SameLine();
				}
			}
			ImGui::Text("MeV");

			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			if (setForCalibration == false)
			{
				ImGui::Text("Energy layer Meterset :");
				ImGui::SameLine();
				for (int j = 0; j < RTPlanEnergyLayerMeterset[i].size(); j++)
				{
					if (j == RTPlanEnergyLayerMeterset[i].size() - 1) ImGui::Text("%0.6f", RTPlanEnergyLayerMeterset[i][j]);
					else if (j == 5 || j == 13 || j == 21 || j == 29 || j == 37 || j == 45 || j == 53 || j == 61 || j == 69 || j == 77 || j == 85) ImGui::Text("%0.6f", RTPlanEnergyLayerMeterset[i][j]);
					else
					{
						ImGui::Text("%0.6f", RTPlanEnergyLayerMeterset[i][j]);
						ImGui::SameLine();
					}
				}
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

				ImGui::Text("Total Meterset : %0.1f", double(std::accumulate(RTPlanEnergyLayerMeterset[i].begin(), RTPlanEnergyLayerMeterset[i].end(), 0.0)));

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);
			}
			ImGui::Text("Snout position : %0.2f (mm)", RTPlanSnoutPosition[i]);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		}

		ImGui::EndChild();
	}

	ImGui::End();

	// ### 3. Process information window ###

	ImGui::SetNextWindowPos(ImVec2(625, 80), ImGuiCond_Always);
	ImGui::SetNextWindowSize(ImVec2(610, 190));
	ImGui::Begin(" Process window", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse);

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

	ImGui::Text("Process status :");

	ImGui::SameLine();

	// Process status branch
	if (RTPlanFileLoaded == false && logFileLoaded == false) ImGui::TextColored(ImVec4(1.f, 0, 0, 1.f), "RT plan, log files are not loaded.");
	else if (RTPlanFileLoaded == false && logFileLoaded == true) ImGui::TextColored(ImVec4(1.f, 0, 0, 1.f), "log files loaded, RT plan is not loaded.");
	else if (RTPlanFileLoaded == true && logFileLoaded == false) ImGui::TextColored(ImVec4(1.f, 0, 0, 1.f), "RT plan is loaded, log files are not loaded.");
	else if (RTPlanFileLoaded == true && logFileLoaded == true && doseMonitorSettingDone == false) ImGui::TextColored(ImVec4(0, 0.8f, 0, 1.f), "RT plan, log files are loaded. Set dose monitor range for each energy layer.");
	else if (RTPlanFileLoaded == true && logFileLoaded == true && doseMonitorSettingDone == true) ImGui::TextColored(ImVec4(0, 0.8f, 0, 1.f), "All Files and dose monitor range is set. Ready to generate code.");

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

	// Button rounding style start
	ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

	if (ImGui::Button("(1) Dose monitor range setting"))
	{
		// Check all data is loaded, mgn name has RT plan's patient ID, mgn's size and energy layers' size is same.
		if (RTPlanFileLoaded == true && logFileLoaded == true)
		{
			int RTPlanSize{ 0 };

			// Check .mgn and .ptn information and RT plan information matched
			for (int i = 0; i < RTPlanNumberOfBeams; i++) RTPlanSize += int(RTPlanEnergyLayer[i].size());
			if (RTPlanSize != mgnFileNameList.size() && !ptnOnlyMode) ImGui::OpenPopup("log-file-and-RTplan-info-not-matched");
			else
			{
				// If dose monitor save button is not pushed, initialize dose monitor setting
				if (doseMonitorSettingDone == true)
				{
					ImGui::OpenPopup("dose-monitor-setting-fixed-error");
				}
				else if (doseMonitorSettingDone == false)
				{
					currentLogMonitorRange.clear();
					currentLogMonitorRange.resize(ptnFileNameList.size());
					ImGui::OpenPopup("Dose-monitor-range-setting-select");
				}
			}

		}
		else ImGui::OpenPopup("data-is-not-ready-error");
	}

	ImGui::SameLine();

	if (ImGui::Button("(2) TOPAS code generate"))
	{
		if (RTPlanFileLoaded == true && logFileLoaded == true && doseMonitorSettingDone == true)
		{
			if (TOPASCodeGenerating == false)
			{
				TOPASCodeGenerating = true;
				std::thread thread(TOPASThread);
				thread.detach();
			}
			else ImGui::OpenPopup("TOPAS-code-already-generating-error");
		}
		else ImGui::OpenPopup("data-load-or-dose-monitor-setting-not-done-error");
	}

	ImGui::SameLine();

	if (ImGui::Button("(3) MOQUI code generate"))
	{
		if (RTPlanFileLoaded == true && logFileLoaded == true && doseMonitorSettingDone == true)
		{
			if (MOQUICodeGenerating == false)
			{
				MOQUICodeGenerating = true;
				std::thread thread(MOQUIThread);
				thread.detach();
			}
			else ImGui::OpenPopup("MOQUI-code-already-generating-error");
		}
		else ImGui::OpenPopup("data-load-or-dose-monitor-setting-not-done-error");
	}

	// TOPAS Code generation related popup
	if (TOPASBaseCodeNotExist == true) ImGui::OpenPopup("TOPAS-base-code-not-exist-error");
	if (folderAlreadyExists == true) ImGui::OpenPopup("folder-already-exist-error");
	if (TOPASCodeGenerateStarted == true)
	{
		ImGui::OpenPopup("TOPAS-code-generate-progress");
		TOPASCodeGenerateStarted = false;
	}
	if (TOPASCodeGenerated == true)
	{
		ImGui::OpenPopup("Notification (TOPAS code generation)");
		TOPASCodeGenerated = false;
	}

	// MOQUI Code generating status
	if (MOQUICodeGenerateStarted == true)
	{
		ImGui::OpenPopup("MOQUI-code-generate-progress");
		MOQUICodeGenerateStarted = false;
	}

	if (MOQUICodeGenerated == true)
	{
		ImGui::OpenPopup("Notification (MOQUI code generation)");
		MOQUICodeGenerated = false;
	}

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

	if (ImGui::Button("All data/setting status reset"))
	{
		// Dose monitor setting reset
		doseMonitorSettingDone = false;

		// RT Plan status reset
		RTPlanBeamNameList.clear();
		RTPlanEnergyLayer.clear();
		RTPlanEnergyLayerMeterset.clear();
		RTPlanSnoutPosition.clear();
		RTPlanDegraderList.clear();
		RTPlanFileLoaded = false;

		// Log file status reset
		mgnFilePathList.clear();
		ptnFilePathList.clear();
		mgnFileNameList.clear();
		ptnFileNameList.clear();

		mgnDataSet.clear();
		ptnDataSet.clear();

		ptnXDataVector.clear();
		ptnYDataVector.clear();
		mgnXDataVector.clear();
		mgnYDataVector.clear();

		particleCountResult.clear();

		ptnSelected = -1;
		logFileLoaded = false;
		doseMonitorRangeManualSettingWindow = false;
		doseMonitorRangeFileSettingWindow = false;
		doseMonitorSettingDone = false;
	}

	ImGui::SameLine();

	if (ImGui::Button("Dose monitor range setting reset"))
	{
		doseMonitorSettingDone = false;
	}

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

	ImGui::TextColored(ImVec4(0, 0, 1, 1), "# Dose monitor value dividing factor setting #");

	ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

	ImGui::RadioButton("Divide by 100 ( > 10,000 )", &doseDividingFactor, 100);
	ImGui::SameLine();
	ImGui::RadioButton("Divide by 10 ( < 10,000 )", &doseDividingFactor, 10);
	ImGui::SameLine();
	ImGui::RadioButton("No divide", &doseDividingFactor, 1);

	// Show the dose monitor range setting select window
	if (ImGui::BeginPopupModal("Dose-monitor-range-setting-select", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 22);
		ImGui::Text("Choose one option to applying dose monitor factor : \n");
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		if (ImGui::Button("Applying from file", ImVec2(130, 0)))
		{
			doseMonitorRangeDialog.SetExtentionInfos(".xlsx", ImVec4(0, 0, 1, 1.0));
			doseMonitorRangeDialog.OpenDialog("ChooseDoseMoniotorRangeFile", "Choose a dose monitor range file", ".xlsx", " ");
			ImGui::CloseCurrentPopup();
		}
		ImGui::SameLine();
		if (ImGui::Button("Applying from manual selecting", ImVec2(220, 0)))
		{
			// Setting value by default dose monitor range 3 
			currentLogMonitorRange.assign(ptnFileNameList.size(), 2);
			doseMonitorRangeManualSettingWindow = true;
			ImGui::CloseCurrentPopup();
		}
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 145);
		if (ImGui::Button("Cancel", ImVec2(80, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// Dose monitor range file dialog display
	if (doseMonitorRangeDialog.Display("ChooseDoseMoniotorRangeFile", ImGuiWindowFlags_NoCollapse, ImVec2(700, 300)))
	{
		if (doseMonitorRangeDialog.IsOk())
		{
			doseMonitorRangeFileFullPath = doseMonitorRangeDialog.GetFilePathName();

			std::filesystem::path p(doseMonitorRangeFileFullPath);

			if (std::filesystem::exists(p) == false) ImGui::OpenPopup("not-valid-dose-monitor-range-file-path-error");
			else if (doseMonitorRangeFileLoading == false)
			{
				doseMonitorRangeFileLoading = true;
				std::thread thread(doseMonitorRangeFileThread);
				thread.detach();
			}
			else if (doseMonitorRangeFileLoading == true)
			{
				ImGui::OpenPopup("Dose-monitor-range-file-now-loading-error");
			}
		}
		doseMonitorRangeDialog.Close();
	}

	// If dose monitor ranger file is already loading, show the error
	if (ImGui::BeginPopupModal("Dose-monitor-range-file-now-loading-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Dose monitor range file is already loading.\nPlease try to load later.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// If dose monitor range file is not found, show the error
	if (ImGui::BeginPopupModal("not-valid-dose-monitor-range-file-path-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Dose monitor range file path you wrote is not availiable.\nPlease check the file path is right.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 110);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// If TOPAS base code folder or files are not found, show the error
	if (ImGui::BeginPopupModal("TOPAS-base-code-not-exist-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("TOPAS base code folder or one of base code is not availiable.\nPlease check the files are ready.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			TOPASBaseCodeNotExist = false;
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// If there are same files already generated, show the error
	if (ImGui::BeginPopupModal("folder-already-exist-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Same patient ID MC code already exist.\nPlease remove the old files before generation.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			folderAlreadyExists = false;
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// TOPAS code generation process popup
	if (ImGui::BeginPopupModal("TOPAS-code-generate-progress", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::ProgressBar(TOPASCodeGenerationProgress, ImVec2(0.0f, 0.0f));
		if (TOPASCodeGenerated == true)
		{
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// TOPAS code generation complete popup
	if (ImGui::BeginPopupModal("Notification (TOPAS code generation)", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("TOPAS code was successfully generated.");
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("Particle count result", ImVec2(300, 200), true);
		ImGui::PopStyleVar();

		ImGui::Text("Generated proton particles --------------------------------------");

		for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
		{
			ImGui::Text("Field %d --------------------------------------------------", i + 1);

			for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
			{
				ImGui::Text("Energy layer %d : ", j + 1);
				ImGui::SameLine();

				if (i == 0)
				{
					unsigned long long particleCount = std::accumulate(particleCountResult[j].begin(), particleCountResult[j].end(), 0LLU);
					ImGui::Text("%llu", particleCount);
				}
				else
				{
					unsigned long long particleCount = std::accumulate(particleCountResult[j + RTPlanEnergyLayer[i - 1].size()].begin(), particleCountResult[j + RTPlanEnergyLayer[i - 1].size()].end(), 0LLU);
					ImGui::Text("%llu", particleCount);
				}
					
			}
		}

		ImGui::EndChild();

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 80);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			particleCountResult.clear();
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// MOQUI code generation process popup
	if (ImGui::BeginPopupModal("MOQUI-code-generate-progress", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::ProgressBar(MOQUICodeGenerationProgress, ImVec2(0.0f, 0.0f));
		if (MOQUICodeGenerated == true)
		{
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// MOQUI code generation complete popup
	if (ImGui::BeginPopupModal("Notification (MOQUI code generation)", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("MOQUI code was successfully generated.");
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

		ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
		ImGui::BeginChild("Particle count result", ImVec2(300, 200), true);
		ImGui::PopStyleVar();

		ImGui::Text("Generated proton particles --------------------------------------");

		for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
		{
			ImGui::Text("Field %d --------------------------------------------------", i + 1);

			for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
			{
				ImGui::Text("Energy layer %d : ", j + 1);
				ImGui::SameLine();

				if (i == 0)
				{
					unsigned long long particleCount = std::accumulate(particleCountResult[j].begin(), particleCountResult[j].end(), 0LLU);
					ImGui::Text("%llu", particleCount);
				}
				else
				{
					unsigned long long particleCount = std::accumulate(particleCountResult[j + RTPlanEnergyLayer[i - 1].size()].begin(), particleCountResult[j + RTPlanEnergyLayer[i - 1].size()].end(), 0LLU);
					ImGui::Text("%llu", particleCount);
				}

			}
		}

		ImGui::EndChild();

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 80);
		if (ImGui::Button("OK", ImVec2(120, 0)))
		{
			particleCountResult.clear();
			ImGui::CloseCurrentPopup();
		}
		ImGui::EndPopup();
	}

	// If dose monitor setting is already done and user attempt to open dose moniter setting, show the error.
	if (ImGui::BeginPopupModal("dose-monitor-setting-fixed-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 150);
		ImGui::Text("Dose monitor setting is fixed.");
		ImGui::Text("Please click dose monitor setting reset button if you need to change the setting.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosY() + 10);
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 115);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If TOPAS code is already being generated, show error
	if (ImGui::BeginPopupModal("TOPAS-code-already-generating-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("TOPAS code is already being generated.\nPlease wait until generation complete.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If TOPAS code is already being generated, show error
	if (ImGui::BeginPopupModal("MOQUI-code-already-generating-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("MOQUI code is already being generated.\nPlease wait until generation complete.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If RT plan and log file data are not ready, show error
	if (ImGui::BeginPopupModal("data-is-not-ready-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 70);
		ImGui::Text("Data is not ready.");
		ImGui::Text("Please load both RT plan and log files.");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 60);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If RT plan and log file data are not matched, show error
	if (ImGui::BeginPopupModal("log-file-and-RTplan-info-not-matched", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Log file and RT plan info not matched.\nPlease load right RT plan and log files.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 60);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// If RT plan and log file data are not matched, show error
	if (ImGui::BeginPopupModal("data-load-or-dose-monitor-setting-not-done-error", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Data is not ready or dose monitor setting is not done.\nPlease check all load and setting process is done.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 110);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}

	// Button rounding style end
	ImGui::PopStyleVar();

	ImGui::End();

	// ### 4. Dose monitor setting window ###

	// Manual setting window
	if (doseMonitorRangeManualSettingWindow == true && RTPlanFileLoaded == true && logFileLoaded == true)
	{
		ImGui::SetNextWindowPos(ImVec2(400, 80), ImGuiCond_Once);
		ImGui::SetNextWindowSize(ImVec2(600, 700));
		ImGui::Begin("Dose monitor setting window", &doseMonitorRangeManualSettingWindow, ImGuiWindowFlags_NoResize);
		ImGui::PushFont(middleFont);
		ImGui::TextColored(ImVec4(0, 0, 1.f, 1.f), "# Dose monitor range specification #");
		ImGui::PopFont();
		ImGui::SameLine();
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 155);

		// Button rounding style start
		ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

		if (ImGui::Button("Save monitor range"))
		{
			ImGui::OpenPopup("dose-monitor-setting-save-popup");
		}

		// Dose monitor setting save button popup
		if (ImGui::BeginPopupModal("dose-monitor-setting-save-popup", NULL, ImGuiWindowFlags_AlwaysAutoResize))
		{
			ImGui::Text("Are you sure to save dose monitor setting? \nYou have to reset the setting if you need to change information of it.\n");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
			if (ImGui::Button("Yes", ImVec2(120, 0)))
			{
				doseMonitorSettingDone = true;
				ImGui::CloseCurrentPopup();
				doseMonitorRangeManualSettingWindow = false;
			}
			ImGui::SameLine();
			if (ImGui::Button("No", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
			ImGui::EndPopup();
		}
		// Button rounding style end
		ImGui::PopStyleVar();

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);
		ImGui::Text("(DOSE_1_RANGE in RT_RECORD_LAYER)");
		ImGui::Text("(1) Dose monitor full range = 160 nA");
		ImGui::Text("(2) Dose monitor full range = 470 nA");
		ImGui::Text("(3) Dose monitor full range = 1400 nA");
		ImGui::Text("(4) Dose monitor full range = 4200 nA");
		ImGui::Text("(5) Dose monitor full range = 12600 nA");
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 15);

		if (ImGui::BeginTabBar("PTNField", ImGuiTabBarFlags_None))
		{
			for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
			{
				std::string fieldNumber = "Field " + std::to_string(i + 1);
				int fieldEnergyLayerCount = int(RTPlanEnergyLayer[i].size());
				int previousLayerCount{ 0 };

				// Get previous layer count
				if (i > 0) for (int k = i - 1; k > -1; k--) previousLayerCount += int(RTPlanEnergyLayer[k].size());

				if (ImGui::BeginTabItem(fieldNumber.c_str()))
				{
					ImGui::Columns(2, "PTNInfo");
					ImGui::Separator();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 105);
					ImGui::Text("Log file name"); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 85);
					ImGui::Text("Dose monitor range"); ImGui::NextColumn();
					ImGui::Separator();
					for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
					{
						ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 45);
						ImGui::Text((ptnFileNameList[previousLayerCount + j]).c_str()); ImGui::NextColumn();
						ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 95);
						ImGui::PushID(std::to_string(previousLayerCount + j).c_str());
						ImGui::SetNextItemWidth(100);
						ImGui::SliderInt("", &currentLogMonitorRange[previousLayerCount + j], 2, 5, "%d", ImGuiSliderFlags_NoInput);
						ImGui::PopID();
						ImGui::NextColumn();
						if (j != RTPlanEnergyLayer[i].size() - 1) ImGui::Separator();
					}
					ImGui::Columns(1);
					ImGui::Separator();
					ImGui::EndTabItem();
				}
			}
			ImGui::EndTabBar();
		}
		ImGui::End();
	}

	// File setting window
	if (doseMonitorRangeFileSettingWindow == true && RTPlanFileLoaded == true && logFileLoaded == true)
	{
		ImGui::SetNextWindowPos(ImVec2(400, 80), ImGuiCond_Once);
		ImGui::SetNextWindowSize(ImVec2(600, 700));
		ImGui::Begin("Dose monitor setting window", &doseMonitorRangeFileSettingWindow, ImGuiWindowFlags_NoResize);
		ImGui::PushFont(middleFont);
		ImGui::TextColored(ImVec4(0, 0, 1.f, 1.f), "# Dose monitor range specification #");
		ImGui::PopFont();
		ImGui::SameLine();
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 180);

		// Button rounding style start
		ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

		if (ImGui::Button("Confirm setting"))
		{
			ImGui::OpenPopup("dose-monitor-setting-confirm-popup");
		}

		// Dose monitor setting save button popup
		if (ImGui::BeginPopupModal("dose-monitor-setting-confirm-popup", NULL, ImGuiWindowFlags_AlwaysAutoResize))
		{
			ImGui::Text("Are you sure to confirm dose monitor setting? \nYou have to reset the setting if you need to change information of it.\n");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 100);
			if (ImGui::Button("Yes", ImVec2(120, 0)))
			{
				doseMonitorSettingDone = true;
				ImGui::CloseCurrentPopup();
				doseMonitorRangeFileSettingWindow = false;
			}
			ImGui::SameLine();
			if (ImGui::Button("No", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
			ImGui::EndPopup();
		}

		// Button rounding style end
		ImGui::PopStyleVar();

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);
		ImGui::Text("(DOSE_1_RANGE in RT_RECORD_LAYER)");
		ImGui::Text("(1) Dose monitor full range = 160 nA");
		ImGui::Text("(2) Dose monitor full range = 470 nA");
		ImGui::Text("(3) Dose monitor full range = 1400 nA");
		ImGui::Text("(4) Dose monitor full range = 4200 nA");
		ImGui::Text("(5) Dose monitor full range = 12600 nA");
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 15);

		if (ImGui::BeginTabBar("PTNField", ImGuiTabBarFlags_None))
		{
			for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
			{
				std::string fieldNumber = "Field " + std::to_string(i + 1);
				int fieldEnergyLayerCount = int(RTPlanEnergyLayer[i].size());
				int previousLayerCount{ 0 };

				// Get previous layer count
				if (i > 0) for (int k = i - 1; k > -1; k--) previousLayerCount += int(RTPlanEnergyLayer[k].size());

				if (ImGui::BeginTabItem(fieldNumber.c_str()))
				{
					ImGui::Columns(2, "PTNInfo");
					ImGui::Separator();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 105);
					ImGui::Text("Log file name"); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 85);
					ImGui::Text("Dose monitor range"); ImGui::NextColumn();
					ImGui::Separator();
					for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
					{
						ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 45);
						ImGui::Text((ptnFileNameList[previousLayerCount + j]).c_str()); ImGui::NextColumn();
						ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 135);
						ImGui::Text("%d", currentLogMonitorRange[previousLayerCount + j]); ImGui::NextColumn();
						if (j < RTPlanEnergyLayer[i].size() - 1) ImGui::Separator();
					}
					ImGui::Columns(1);
					ImGui::Separator();
					ImGui::EndTabItem();
				}
			}
			ImGui::EndTabBar();
		}
		ImGui::End();
	}

	// If dose monitor range file has not right length, show the error
	if (doseMonitorRangeFileLengthNotFit == true)
	{
		ImGui::OpenPopup("dose-monitor-range-file-length-not-fit");
		doseMonitorRangeFileLengthNotFit = false;
	}
	if (ImGui::BeginPopupModal("dose-monitor-range-file-length-not-fit", NULL, ImGuiWindowFlags_AlwaysAutoResize))
	{
		ImGui::Text("Dose monitor range excel file has not right length for current log file.\nPlease check the excel information is right.\n");
		ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 145);
		if (ImGui::Button("OK", ImVec2(120, 0))) ImGui::CloseCurrentPopup();
		ImGui::EndPopup();
	}
}

// Rendering speical window by menu click
void getExtraFunctionWidget()
{
	// PTN file information window
	if (showPtnRawValue)
	{
		ImGui::SetNextWindowPos(ImVec2(200, 200), ImGuiCond_Appearing);
		ImGui::SetNextWindowSize(ImVec2(600, 620));
		ImGui::Begin("PTN file information view window", NULL, ImGuiWindowFlags_NoResize);

		if (logFileLoaded == false && logFileLoading == false)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file not loaded");
			ImGui::PopFont();
			ImGui::EndChild();
			ImGui::PopStyleVar();
		}
		else if (logFileLoaded == false && logFileLoading == true)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::PopStyleVar();
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 200);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file is being loaded");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 220);
			ImGui::Text("Please wait..");
			ImGui::PopFont();
			ImGui::EndChild();

		}
		else if (logFileLoaded == true)
		{
			if (ptnSelected != -1)
			{

				ImGui::Text("Log file name : %s", ptnFileNameList[ptnSelected].c_str());
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				// Button rounding style start
				ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

				if (ImGui::Button("Save as a excel file"))
				{
					logFileExcelSaving = true;
					savePtnAsExcel = true;
					ImGui::OpenPopup("Log-file-saving-progress");
					std::thread thread(logFileExcelSaveThread);
					thread.detach();
				}

				// Button rounding style end
				ImGui::PopStyleVar();

				// TOPAS code generation process popup
				if (ImGui::BeginPopupModal("Log-file-saving-progress", NULL, ImGuiWindowFlags_AlwaysAutoResize))
				{
					ImGui::Text("Log file is saving. please wait...");
					if (logFileExcelSaving == false)
					{
						ImGui::CloseCurrentPopup();
					}
					ImGui::EndPopup();
				}

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				ImGui::BeginChild("Log file value child window", ImVec2(584, 500), false, ImGuiWindowFlags_None);

				ImGui::Columns(4, "Log file value table");
				ImGui::Separator();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("Time (ms)"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("X position"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("Y position"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("MU count"); ImGui::NextColumn();
				ImGui::Separator();
				for (int i = 0; i < ptnTimeDataVector.size(); i++)
				{
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.3f", ptnTimeDataVector[i]); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.3f", ptnXDataVector[i]); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.3f", ptnYDataVector[i]); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 50);
					ImGui::Text("%.0f", ptnDoseMonitorDataVector[i]); ImGui::NextColumn();
				}
				ImGui::Columns(1);
				ImGui::Separator();

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 20 );
				ImGui::Columns(1, "Total MU count title");
				ImGui::Separator();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 255);
				ImGui::Text("Total MU count");
				ImGui::Columns(1);

				ImGui::Columns(1, "Total MU count");
				ImGui::Separator();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 255);
				unsigned long long particleCount = std::accumulate(ptnDoseMonitorDataVector.begin(), ptnDoseMonitorDataVector.end(), 0LLU);
				ImGui::Text("%llu", particleCount);
				ImGui::Columns(1);
				ImGui::Separator();

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
				ImGui::EndChild();
			}
			else
			{
				ImGui::Text("Log file name : Log file not selected");
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

				ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
				ImGui::BeginChild("Logfile raw value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
				ImGui::PopStyleVar();
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 180);
				ImGui::PushFont(bigFont);
				ImGui::Text("Please select the log file");
				ImGui::PopFont();
				ImGui::EndChild();
			}

		}

		ImGui::End();
	}

	// MGN file information window
	if (showMgnRawValue && !ptnOnlyMode)
	{
		ImGui::SetNextWindowPos(ImVec2(200, 200), ImGuiCond_Appearing);
		ImGui::SetNextWindowSize(ImVec2(600, 600));
		ImGui::Begin("MGN file information view window", NULL, ImGuiWindowFlags_NoResize);

		if (logFileLoaded == false && logFileLoading == false)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file not loaded");
			ImGui::PopFont();
			ImGui::EndChild();
			ImGui::PopStyleVar();
		}
		else if (logFileLoaded == false && logFileLoading == true)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::PopStyleVar();
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 200);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file is being loaded");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 220);
			ImGui::Text("Please wait..");
			ImGui::PopFont();
			ImGui::EndChild();

		}
		else if (logFileLoaded == true)
		{
			if (ptnSelected != -1)
			{

				ImGui::Text("Log file name : %s", mgnFileNameList[ptnSelected].c_str());
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				ImGui::Text("Selected log file's line segment count : %d", mgnTimeDataVector.size() - 2);
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				// Button rounding style start
				ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

				if (ImGui::Button("Save as a excel file"))
				{
					logFileExcelSaving = true;
					saveMgnAsExcel = true;
					ImGui::OpenPopup("Log-file-saving-progress");
					std::thread thread(logFileExcelSaveThread);
					thread.detach();
				}
				// Button rounding style end
				ImGui::PopStyleVar();


				// TOPAS code generation process popup
				if (ImGui::BeginPopupModal("Log-file-saving-progress", NULL, ImGuiWindowFlags_AlwaysAutoResize))
				{
					ImGui::Text("Log file is saving. please wait...");
					if (logFileExcelSaving == false)
					{
						ImGui::CloseCurrentPopup();
					}
					ImGui::EndPopup();
				}

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				ImGui::BeginChild("Log file value child window", ImVec2(584, 465), false, ImGuiWindowFlags_None);

				ImGui::Columns(4, "Log file value table");
				ImGui::Separator();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 10);
				ImGui::Text("Segment number"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("Time (ms)"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("X Position"); ImGui::NextColumn();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
				ImGui::Text("Y Position"); ImGui::NextColumn();
				ImGui::Separator();
				for (int i = 0; i < mgnTimeDataVector.size(); i++)
				{
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 50);
					ImGui::Text("%d", i + 1); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.1f", mgnTimeDataVector[i]); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.3f", mgnXDataVector[i]); ImGui::NextColumn();
					ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
					ImGui::Text("%.3f", mgnYDataVector[i]); ImGui::NextColumn();
				}
				ImGui::Columns(1);
				ImGui::Separator();

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
				ImGui::EndChild();
			}
			else
			{
				ImGui::Text("Log file name : Log file not selected");
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

				ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
				ImGui::BeginChild("Logfile raw value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
				ImGui::PopStyleVar();
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 180);
				ImGui::PushFont(bigFont);
				ImGui::Text("Please select the log file");
				ImGui::PopFont();
				ImGui::EndChild();
			}

		}

		ImGui::End();
	}

	if (showLogDivWindow)
	{
		ImGui::SetNextWindowPos(ImVec2(200, 200), ImGuiCond_Appearing);
		ImGui::SetNextWindowSize(ImVec2(600, 600));
		ImGui::Begin("Log file division window", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoScrollWithMouse);

		if (logFileLoaded == false && logFileLoading == false)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file not loaded");
			ImGui::PopFont();
			ImGui::EndChild();
			ImGui::PopStyleVar();
		}
		else if (logFileLoaded == false && logFileLoading == true)
		{
			ImGui::Text("Log file name : Not loaded");
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

			ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
			ImGui::BeginChild("Logfile value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
			ImGui::PopStyleVar();
			ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 200);
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 200);
			ImGui::PushFont(bigFont);
			ImGui::Text("Log file is being loaded");
			ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 220);
			ImGui::Text("Please wait..");
			ImGui::PopFont();
			ImGui::EndChild();
		}
		else if (logFileLoaded == true)
		{
			if (ptnSelected != -1)
			{

				ImGui::Text("Log file name : %s", ptnFileNameList[ptnSelected].c_str());
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				ImGui::Text("Selected log file's line segment count : %d", mgnTimeDataVector.size()-2);

				ImGui::SameLine();
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 30);

				// Button rounding style start
				ImGui::PushStyleVar(ImGuiStyleVar_FrameRounding, 5.0f);

				if (ImGui::Button("Save line segments as log files"))
				{
					logFileDivSaving = true;
					ImGui::OpenPopup("Div-Log-file-saving-progress");
					std::thread thread(logFileDivSaveThread);
					thread.detach();
				}

				// Button rounding style end
				ImGui::PopStyleVar();

				// TOPAS code generation process popup
				if (ImGui::BeginPopupModal("Div-Log-file-saving-progress", NULL, ImGuiWindowFlags_AlwaysAutoResize))
				{
					ImGui::Text("Divided log file is saving. please wait...");
					if (logFileDivSaving == false)
					{
						ImGui::CloseCurrentPopup();
					}
					ImGui::EndPopup();
				}

				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);

				if (ImGui::BeginTabBar("PTN file info per line segment", ImGuiTabBarFlags_FittingPolicyScroll))
				{
					for (int i = 0; i < mgnTimeDataVector.size() - 2; i++)
					{
						std::string tapItemName = "Segment " + std::to_string(i + 1);

						if (ImGui::BeginTabItem(tapItemName.c_str()))
						{
							float segmentStart = mgnTimeDataVector[i + 1];
							float segmentEnd = mgnTimeDataVector[i + 2];

							ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

							ImGui::BeginChild("Log file value child window", ImVec2(584, 460), false, ImGuiWindowFlags_None);

							ImGui::Columns(4, "Log file value table");
							ImGui::Separator();
							ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
							ImGui::Text("Time (ms)"); ImGui::NextColumn();
							ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
							ImGui::Text("X position"); ImGui::NextColumn();
							ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
							ImGui::Text("Y position"); ImGui::NextColumn();
							ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 35);
							ImGui::Text("MU count"); ImGui::NextColumn();
							ImGui::Separator();

							for (int j = 0; j < ptnTimeDataVector.size(); j++)
							{
								if (ptnTimeDataVector[j] >= segmentStart && ptnTimeDataVector[j] < segmentEnd)
								{
									ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
									ImGui::Text("%.3f", ptnTimeDataVector[j]); ImGui::NextColumn();
									ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
									ImGui::Text("%.3f", ptnXDataVector[j]); ImGui::NextColumn();
									ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 40);
									ImGui::Text("%.3f", ptnYDataVector[j]); ImGui::NextColumn();
									ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 50);
									ImGui::Text("%.0f", ptnDoseMonitorDataVector[j]); ImGui::NextColumn();
								}
							}
							ImGui::Columns(1);
							ImGui::Separator();

							ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

							ImGui::EndChild();
							ImGui::EndTabItem();
						}
					}
					ImGui::EndTabBar();
				}
			}
			else
			{
				ImGui::Text("Log file name : Log file not selected");
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 5);

				ImGui::PushStyleVar(ImGuiStyleVar_ChildRounding, 5.0f);
				ImGui::BeginChild("Logfile raw value child window", ImVec2(584, 535), true, ImGuiWindowFlags_None);
				ImGui::PopStyleVar();
				ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 230);
				ImGui::SetCursorPosX(ImGui::GetCursorPosX() + 180);
				ImGui::PushFont(bigFont);
				ImGui::Text("Please select the log file");
				ImGui::PopFont();
				ImGui::EndChild();
			}

		}

		ImGui::End();
	}
}