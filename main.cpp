#include "mainheader.h"

// Gaussian function for beam parameter interpolation
double gaussianFunc(double x)
{
	double y = 0.7224 * std::exp(-std::pow(((x - 82.75) / 168.5), 2));
	return y;
}

int CALLBACK WinMain(__in HINSTANCE hInstance, __in HINSTANCE hPrevInstance, __in LPSTR lpCmdLine, __in int nCmdShow)
{
	// Hiding console window. when debug needed, just comment it
	//HWND hWndConsole = GetConsoleWindow();
	//ShowWindow(hWndConsole, SW_HIDE);

	// Log file interpretation related value reading
	std::ifstream G2InitValueList("./scv_init_G1.txt");
	std::stringstream stream;
	std::vector<std::string> stringDigitSet;
	std::string line;
	std::string word;

	if (G2InitValueList.is_open())
	{
		while (!G2InitValueList.eof())
		{
			std::getline(G2InitValueList, line);

			if (line.rfind("XPRESETOFFSET", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); XPRESETOFFSET = stof(stringDigitSet[1]); }
			if (line.rfind("YPRESETOFFSET", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); YPRESETOFFSET = stof(stringDigitSet[1]); }
			if (line.rfind("XPRESETGAIN", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); XPRESETGAIN = stof(stringDigitSet[1]); }
			if (line.rfind("YPRESETGAIN", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); YPRESETGAIN = stof(stringDigitSet[1]); }
			if (line.rfind("TIMEGAIN", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); TIMEGAIN = stof(stringDigitSet[1]); }
			if (line.rfind("XPOSOFFSET", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); XPOSOFFSET = stof(stringDigitSet[1]); }
			if (line.rfind("YPOSOFFSET", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); YPOSOFFSET = stof(stringDigitSet[1]); }
			if (line.rfind("XPOSGAIN", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); XPOSGAIN = stof(stringDigitSet[1]); }
			if (line.rfind("YPOSGAIN", 0) == 0) { stream.str(line); while (stream >> word) stringDigitSet.push_back(word); YPOSGAIN = stof(stringDigitSet[1]); }

			stream.clear();
			stringDigitSet.clear();
		}

		G2InitValueList.close();
	}
	else
	{
		std::cout << "Log file interpretation code not found" << std::endl;
		return -1;
	}

	int displayW{};
	int displayH{};

	/* Show loading page before program start */ 
	clock_t loadingStartTime, loadingEndTime;
	double loadingSecondCount{ 0.f };
	int loadingMonitorCount, loadingMonitorX, loadinMonitorY{};
	bool loadingScreenOff{ false };

	// GLFW window initialization
	glfwInit();
	GLFWwindow* loadingWindow;
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
	glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
	glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
	glfwWindowHint(GLFW_DECORATED, GLFW_FALSE);
	glfwWindowHint(GLFW_RESIZABLE, GL_FALSE);
	glfwWindowHint(GLFW_TRANSPARENT_FRAMEBUFFER, 1);

	// Get monitor position
	GLFWmonitor** loadingMonitors = glfwGetMonitors(&loadingMonitorCount);
	const GLFWvidmode* loadingVideoMode = glfwGetVideoMode(loadingMonitors[0]);
	glfwGetMonitorPos(loadingMonitors[0], &loadingMonitorX, &loadinMonitorY);

	// Create GLFW window
	loadingWindow = glfwCreateWindow(700, 340, "SMC Pretreatment QA loading window", nullptr, nullptr);
	glfwMakeContextCurrent(loadingWindow);

	// GLFW hint initialization
	glfwDefaultWindowHints();

	// Show GLFW window again width relatively center
	glfwSetWindowPos(loadingWindow, loadingMonitorX + (loadingVideoMode->width - 700) / 2, loadinMonitorY + (loadingVideoMode->height - 340) / 2);
	glfwShowWindow(loadingWindow);

	// OpenGL init
	gl3wInit();

	// ImGui init
	IMGUI_CHECKVERSION();
	ImGui::CreateContext();
	ImGuiIO& loadingIO = ImGui::GetIO();

	ImGui::StyleColorsLight();
	ImGui::GetIO().IniFilename = nullptr;

	ImGui_ImplGlfw_InitForOpenGL(loadingWindow, true);
	ImGui_ImplOpenGL3_Init("#version 430 core");

	// Fonts loading
	loadingIO.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 20.0f);
	loadingIO.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 25.0f);
	loadingIO.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 17.0f);

	GLuint loadingLogo1Tex, loadingLogo2Tex{};
	int logo1Width, logo1Height, logo2Width, logo2Height{};

	bool ret1 = LoadTextureFromFile("./source/loading_logo1.png", &loadingLogo1Tex, &logo1Width, &logo1Height);
	bool ret2 = LoadTextureFromFile("./source/loading_logo2.png", &loadingLogo2Tex, &logo2Width, &logo2Height);
	IM_ASSERT(ret1);
	IM_ASSERT(ret2);

	// Start the clock
	loadingStartTime = clock();

	while (!loadingScreenOff)
	{
		ImGui_ImplOpenGL3_NewFrame();
		ImGui_ImplGlfw_NewFrame();
		ImGui::NewFrame();

		loadingEndTime = clock();
		loadingSecondCount = double(loadingEndTime - loadingStartTime);
		if ((loadingSecondCount / CLOCKS_PER_SEC) > 5.f) loadingScreenOff = true;

		ImGui::SetNextWindowSize(ImVec2(680, 320));
		ImGui::SetNextWindowPos(ImVec2((700 - 680) / 2, (350 - 320) / 2));
		ImGui::Begin("Loading window", NULL, ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoResize);
		
		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 30);
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - 211) / 2);
		ImGui::Image((void*)(intptr_t)loadingLogo1Tex, ImVec2(211, 66));

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 15);
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - 434) / 2);
		ImGui::Image((void*)(intptr_t)loadingLogo2Tex, ImVec2(434, 27));

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 35);
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - ImGui::CalcTextSize("Chanil Jeon, Jinhyeop Lee, Jungwook Shin, Wonjoong Cheon").x) / 2);
		ImGui::Text("Chanil Jeon, Jinhyeop Lee, Jungwook Shin, Wonjoong Cheon");
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - ImGui::CalcTextSize("Sunghwan Ahn, Kwanghyun Jo, Youngyih Han*").x) / 2);
		ImGui::Text("Sunghwan Ahn, Kwanghyun Jo, Youngyih Han*");

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		ImGui::PushFont(loadingIO.Fonts->Fonts[2]);
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - ImGui::CalcTextSize("Published in Medical Physics V50, Issue 11 (p 7139-7153)").x) / 2);
		ImGui::TextColored(ImVec4(1.f, 0.f, 0.f, 1.f), "Published in Medical Physics V50, Issue 11 (p 7139-7153)");
		ImGui::PopFont();

		ImGui::SetCursorPosY(ImGui::GetCursorPosY() + 10);
		ImGui::PushFont(loadingIO.Fonts->Fonts[2]);
		ImGui::SetCursorPosX((ImGui::GetWindowSize().x - ImGui::CalcTextSize("Programmed by Chanil Jeon").x) / 2);
		ImGui::Text("Programmed by Chanil Jeon");
		ImGui::PopFont();

		ImGui::End();

		ImGui::Render();

		glfwMakeContextCurrent(loadingWindow);
		glfwGetFramebufferSize(loadingWindow, &displayW, &displayH);

		glViewport(0, 0, displayW, displayH);
		glClearColor(0.f, 0.f, 0.f, 0.f);
		glClear(GL_COLOR_BUFFER_BIT);

		ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
		glfwSwapBuffers(loadingWindow);
		glfwPollEvents();
	}

	ImGui_ImplOpenGL3_Shutdown();
	ImGui_ImplGlfw_Shutdown();
	ImGui::DestroyContext();
	glfwDestroyWindow(loadingWindow);
	glfwTerminate();

	/* Start main program ------------------------------------------------------------------------ */

	// GLFW Initialization
	glfwInit();
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
	glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
	glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
	glfwWindowHint(GLFW_RESIZABLE, GL_FALSE);

	int monitorCount, monitorX, monitorY{};

	GLFWwindow* GUIWindow;
	GLFWmonitor** monitors = glfwGetMonitors(&monitorCount);
	const GLFWvidmode* videoMode = glfwGetVideoMode(monitors[0]);
	glfwGetMonitorPos(monitors[0], &monitorX, &monitorY);

	GUIWindow = glfwCreateWindow(1245, 900, "SMC Pretreatment QA", nullptr, nullptr);
	glfwMakeContextCurrent(GUIWindow);

	// GLFW hint initialization
	glfwDefaultWindowHints();

	// Show GLFW window again width relatively center
	glfwSetWindowPos(GUIWindow, monitorX + (videoMode->width - 1245) / 2, monitorY + (videoMode->height - 900) / 2);
	glfwShowWindow(GUIWindow);

	GLFWimage image[1];
	image[0].pixels = stbi_load("./source/quality-assurance.png", &image[0].width, &image[0].height, 0, 4);
	glfwSetWindowIcon(GUIWindow, 1, image);
	stbi_image_free(image[0].pixels);

	// GL3W Initialization
	gl3wInit();

	// ImGui Initialization
	IMGUI_CHECKVERSION();
	ImGui::CreateContext();
	ImGuiIO& io = ImGui::GetIO();

	ImGui::StyleColorsLight();
	ImGui::GetStyle().WindowRounding = 10.0f;
	ImGui::GetIO().IniFilename = nullptr;

	ImGui_ImplGlfw_InitForOpenGL(GUIWindow, true);
	ImGui_ImplOpenGL3_Init("#version 430 core");

	// Fonts loading
	basicFont = io.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 16.0f);
	bigFont = io.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 25.0f);
	middleFont = io.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 20.0f);
	smallFont = io.Fonts->AddFontFromFileTTF("./Roboto-Medium.ttf", 13.0f);

	// Logo loading
	int logo_width{ 434 };
	int logo_height{ 27 };
	GLuint logo_texture{};
	bool ret = LoadTextureFromFile("./source/logo.png", &logo_texture, &logo_width, &logo_height);
	IM_ASSERT(ret);

	while (!glfwWindowShouldClose(GUIWindow))
	{
		ImGui_ImplOpenGL3_NewFrame();
		ImGui_ImplGlfw_NewFrame();
		ImGui::NewFrame();

		// Components
		getMenu();
		getLogoAndAuthor(&logo_texture, &logo_width, &logo_height);
		getDefaultWidget();
		getExtraFunctionWidget();

		// Render whole components
		ImGui::Render();

		glfwMakeContextCurrent(GUIWindow);
		glfwGetFramebufferSize(GUIWindow, &displayW, &displayH);

		glViewport(0, 0, displayW, displayH);
		glClearColor(0.9f, 0.9f, 0.9f, 1.f);
		glClear(GL_COLOR_BUFFER_BIT);

		ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
		glfwSwapBuffers(GUIWindow);

		glfwPollEvents();
	}

	ImGui_ImplOpenGL3_Shutdown();
	ImGui_ImplGlfw_Shutdown();
	ImGui::DestroyContext();

	glfwDestroyWindow(GUIWindow);
	glfwTerminate();

	return 0;
}

// Load DICOM RT plan file
void RTPlanLoadingThread()
{
	if (RTPlanLoading == true)
	{
		imebra::DataSet RTPlanDataSet(imebra::CodecFactory::load(RTplanfileFullPath));

		/* Get modality form identifying RTPLAN */
		imebra::ReadingDataHandler modalityReader = RTPlanDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::Modality_0008_0060), 0);
		std::wstring modalityWstring = modalityReader.getUnicodeString(0);
		modality.assign(modalityWstring.begin(), modalityWstring.end());

		if (modality != "RTPLAN")
		{
			RTPlanLoading = false;
			modalityErrorFlag = true;
		}
		else
		{
			/* Get RT plan patientID (300A, 0020) */
			imebra::ReadingDataHandler RTPlanPatientIReader = RTPlanDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::PatientID_0010_0020), 0);
			std::wstring RTPlanPatientIDWstring = RTPlanPatientIReader.getUnicodeString(0);

			// Unicode string to ANSI string
			RTPlanPatientID.assign(RTPlanPatientIDWstring.begin(), RTPlanPatientIDWstring.end());

			/* Get RT plan date (300A, 0006) */
			imebra::ReadingDataHandler RTPlanDateReader = RTPlanDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::RTPlanDate_300A_0006), 0);
			std::wstring RTPlanDateWstring = RTPlanDateReader.getUnicodeString(0);
			RTPlanDate.assign(RTPlanDateWstring.begin(), RTPlanDateWstring.end());

			/* Get RT plan name (300A, 0003) */
			imebra::ReadingDataHandler RTPlanNameReader = RTPlanDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::RTPlanName_300A_0003), 0);
			std::wstring RTPlanNameWstring = RTPlanNameReader.getUnicodeString(0);
			RTPlanName.assign(RTPlanNameWstring.begin(), RTPlanNameWstring.end());

			/* Get fraction group sequence dataset (300A, 0070) */
			imebra::DataSet RTPlanFractionGroupSequenceDataSet = RTPlanDataSet.getSequenceItem(imebra::TagId(imebra::tagId_t::FractionGroupSequence_300A_0070), 0);
			imebra::ReadingDataHandler RTPlanNumberOfBeamsReader = RTPlanFractionGroupSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::NumberOfBeams_300A_0080), 0);
			std::wstring RTPlanNumberOfBeamsWstring = RTPlanNumberOfBeamsReader.getUnicodeString(0);
			RTPlanNumberOfBeams = std::stoi(RTPlanNumberOfBeamsWstring);

			/* Get ion beam sequence dataset (300A, 03A2) */
			for (int i = 0; i < RTPlanNumberOfBeams; i++)
			{
				imebra::DataSet RTPlanIonBeamSequenceDataSet = RTPlanDataSet.getSequenceItem(imebra::TagId(12298, 0, 930), i);

				// RT Plan beam name load (300A, 00C2)
				imebra::ReadingDataHandler RTPlanBeamNameReader = RTPlanIonBeamSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::BeamName_300A_00C2), 0);
				std::wstring RTPlanBeamNameWstring = RTPlanBeamNameReader.getUnicodeString(0);
				std::string RTPlanBeamName;
				RTPlanBeamName.assign(RTPlanBeamNameWstring.begin(), RTPlanBeamNameWstring.end());
				RTPlanBeamNameList.push_back(RTPlanBeamName);

				// Get number of control point for loop (300A, 0110)
				imebra::ReadingDataHandler RTPlanNumberOfControlPointReader = RTPlanIonBeamSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::NumberOfControlPoints_300A_0110), 0);
				std::wstring RTPlanCurrentNumberOfBeamControlPointWstring = RTPlanNumberOfControlPointReader.getUnicodeString(0);
				int RTPlanCurrentNumberOfBeamControlPoint = stoi(RTPlanCurrentNumberOfBeamControlPointWstring);

				// Get range shifter sequence. if there is not rangeshifter sequence, catch the error and push back "No degrader"
				try
				{
					RTPlanIonBeamSequenceDataSet.getSequenceItem(imebra::TagId(imebra::tagId_t::RangeShifterSequence_300A_0314), 0);
					RTPlanDegraderList.push_back("Degrader");
				}
				catch (imebra::MissingTagError e)
				{
					RTPlanDegraderList.push_back("No Degrader");
				}

				// Temporal value for comparing overlap layer
				std::wstring previousEnergyLayer{L""};
				std::wstring previousEnergyLayerMeterset{L""};

				// Get all energy layer information from each field
				for (int j = 0; j < RTPlanCurrentNumberOfBeamControlPoint; j++)
				{
					// Get control point sequence (300A, 03A8)
					imebra::DataSet RTPlanControlPointSequenceDataSet = RTPlanIonBeamSequenceDataSet.getSequenceItem(imebra::TagId(imebra::tagId_t::IonControlPointSequence_300A_03A8), j);

					// Get nominal energy unit once, snout position for each field
					if (j == 0)
					{
						if (i == 0)
						{
							// Get nominal beam energy unit (300A, 0015)
							imebra::ReadingDataHandler RTPlanNominalEnergyUnitReader = RTPlanControlPointSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::NominalBeamEnergyUnit_300A_0015), 0);
							std::wstring RTPlanBeamEnergyUnitWstring = RTPlanNominalEnergyUnitReader.getUnicodeString(0);
							RTPlanBeamEnergyUnit.assign(RTPlanBeamEnergyUnitWstring.begin(), RTPlanBeamEnergyUnitWstring.end());
						}

						// Get snout position (300A, 030D)
						imebra::ReadingDataHandler RTPlanSnoutPositionReader = RTPlanControlPointSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::SnoutPosition_300A_030D), 0);
						float RTPlanSnoutPositionTemp = RTPlanSnoutPositionReader.getFloat(0);
						RTPlanSnoutPosition.push_back(RTPlanSnoutPositionTemp);
					}

					// Get nominal energy (300A, 0114)
					imebra::ReadingDataHandler RTPlanNominalEnergyReader = RTPlanControlPointSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::NominalBeamEnergy_300A_0114), 0);
					std::wstring RTPlanNominalEnergyWstring = RTPlanNominalEnergyReader.getUnicodeString(0);

					if (setForCalibration == false)
					{
						// Get cumulative meterset weight, and calculate MU of each energy layer (300A, 0134)
						imebra::ReadingDataHandler RTPlanEnergyLayerMetersetReader = RTPlanControlPointSequenceDataSet.getReadingDataHandler(imebra::TagId(imebra::tagId_t::CumulativeMetersetWeight_300A_0134), 0);
						std::wstring RTPlanEnergyLayerMetersetWstring = RTPlanEnergyLayerMetersetReader.getUnicodeString(0);

						if (j > 0)
						{
							if (RTPlanEnergyLayerMetersetWstring != previousEnergyLayerMeterset)
							{
								if (previousEnergyLayerMeterset == L"") previousEnergyLayerMeterset = L"0";
								float RTPlanEnergyLayerMetersetFloat = stof(RTPlanEnergyLayerMetersetWstring) - stof(previousEnergyLayerMeterset);
								RTPlanEnergyLayerMetersetTemp.push_back(RTPlanEnergyLayerMetersetFloat);
							}
						}
						previousEnergyLayerMeterset = RTPlanEnergyLayerMetersetWstring;

						if (RTPlanNominalEnergyWstring != previousEnergyLayer)
						{
							RTPlanEnergyLayerTemp.push_back(stof(RTPlanNominalEnergyWstring));
						}
					}
					else
					{
						if (calibModeMultiEnergyLayer)
						{
							if (RTPlanNominalEnergyWstring != previousEnergyLayer)
							{
								RTPlanEnergyLayerTemp.push_back(stof(RTPlanNominalEnergyWstring));
							}
						}
						else RTPlanEnergyLayerTemp.push_back(stof(RTPlanNominalEnergyWstring));
					}
					
						
					previousEnergyLayer = RTPlanNominalEnergyWstring;
				}

				RTPlanEnergyLayer.push_back(RTPlanEnergyLayerTemp);
				RTPlanEnergyLayerTemp.clear();

				if (setForCalibration == false)
				{
					RTPlanEnergyLayerMeterset.push_back(RTPlanEnergyLayerMetersetTemp);
					RTPlanEnergyLayerMetersetTemp.clear();
				}
			}

			RTPlanFileLoaded = true;
			RTPlanLoading = false;
		}
	}
	return;
}

// Load MGN, PTN file
void logFileLoadingThread()
{
	if (logFileLoading == true)
	{
		int mgnLogCount = 0;
		int ptnLogCount = 0;

		std::filesystem::path p(logFileFolderPath);

		// Get log file list
		for (const std::filesystem::directory_entry& entry :
			std::filesystem::directory_iterator(p)) {
			if (entry.path().extension() == ".ptn")
			{
				ptnFilePathList.push_back(entry.path().string());
				ptnFileNameList.push_back(entry.path().filename().string());
				ptnLogCount++;
			}
			else if (entry.path().extension() == ".mgn" && !ptnOnlyMode)
			{
				mgnFilePathList.push_back(entry.path().string());
				mgnFileNameList.push_back(entry.path().filename().string());
				mgnLogCount++;
			}
		}

		// If log file has no ptn or no mgn or both
		if (ptnLogCount == 0 || mgnLogCount == 0 && !ptnOnlyMode)
		{
			mgnFilePathList.clear();
			ptnFilePathList.clear();
			mgnFileNameList.clear();
			ptnFileNameList.clear();
			logFileNotIncluded = true;
			logFileLoading = false;
		}
		// If log file is not matched, show not match error
		else if (ptnLogCount != mgnLogCount && !ptnOnlyMode)
		{
			mgnFilePathList.clear();
			ptnFilePathList.clear();
			mgnFileNameList.clear();
			ptnFileNameList.clear();
			logFileNotMatch = true;
			logFileLoading = false;
		}
		else if (ptnLogCount == 0 && ptnOnlyMode)
		{
			mgnFilePathList.clear();
			ptnFilePathList.clear();
			mgnFileNameList.clear();
			ptnFileNameList.clear();
			logFileNotIncluded = true;
			logFileLoading = false;
		}
		// If it is not catched by error handling, load the log files
		else
		{
			if (!ptnOnlyMode)
			{
				// Read MGN file
				for (int i = 0; i < mgnFilePathList.size(); i++)
				{
					std::ifstream inputLogFileMGN(mgnFilePathList[i], std::ios::in | std::ios::binary);
					if (inputLogFileMGN.is_open())
					{
						// Extract file's length from seekg
						inputLogFileMGN.seekg(0, inputLogFileMGN.end);
						int length = (int)inputLogFileMGN.tellg();
						inputLogFileMGN.seekg(0, inputLogFileMGN.beg);

						// Make temporal xtensor array with 8-bit divided
						int modifiedLength = length / 2 / 7 * 6;
						std::vector<size_t> MGNShape = { 1, unsigned int(modifiedLength) };
						xt::xarray<float> mgnDataArray(MGNShape);

						// Get each 4 byte data from file
						for (int i = 0; i < modifiedLength; i++)
						{
							// Read time (4 bytes)
							if (i % 6 == 0)
							{
								// Read time [us]
								unsigned int time{};
								inputLogFileMGN.read(reinterpret_cast<char*>(&time), sizeof(time));
								mgnDataArray[i] = float(ntohl(time));
							}
							else // Read else component (X, Y, Beam on/off) (2 bytes)
							{
								unsigned short elseComponent{};
								inputLogFileMGN.read(reinterpret_cast<char*>(&elseComponent), sizeof(elseComponent));
								mgnDataArray[i] = float(ntohs(elseComponent));
							}
						}

						// Change shape to six columns per each row (time[us], ?, ?, X position, Y position, Beam on/off)
						mgnDataArray.reshape({ -1, 6 });

						// X, Y position conversion (mm)
						// xt::range [min, max), so choose 3,4 like this way
						auto mgnPositionXView = xt::view(mgnDataArray, xt::all(), xt::range(3, 4));
						auto mgnPositionYView = xt::view(mgnDataArray, xt::all(), xt::range(4, 5));
						mgnPositionXView = (mgnPositionXView - XPRESETOFFSET) * XPRESETGAIN;
						mgnPositionYView = (mgnPositionYView - YPRESETOFFSET) * YPRESETGAIN;

						mgnDataSet.push_back(mgnDataArray);
					}
					else std::cout << "System failed to open path :" << mgnFilePathList[i] << std::endl;

					inputLogFileMGN.close();
				}
			}
			
			// Read PTN files
			for (int i = 0; i < ptnFilePathList.size(); i++)
			{
				std::ifstream inputLogFilePTN(ptnFilePathList[i], std::ios::in | std::ios::binary);

				if (inputLogFilePTN.is_open())
				{
					// Extract file's length from seekg
					inputLogFilePTN.seekg(0, inputLogFilePTN.end);
					int length = (int)inputLogFilePTN.tellg();
					inputLogFilePTN.seekg(0, inputLogFilePTN.beg);

					// Make temporal xtensor array with 8-bit divided
					int modifiedLength = length / 2;
					std::vector<size_t> PTNShape = { 1, unsigned int(modifiedLength) };
					xt::xarray<float> ptnDataArray(PTNShape);

					for (int i = 0; i < modifiedLength; i++)
					{
						unsigned short component{};
						inputLogFilePTN.read(reinterpret_cast<char*>(&component), sizeof(component));
						ptnDataArray[i] = float(ntohs(component));
					}

					// Change shape to eight columns per each row (X [mm], Y[mm], X size[mm], Y size[mm], Dose 1[a.u.], Dose 2[a.u.], layer number, Beam On/Off) 
					ptnDataArray.reshape({ -1, 8 });

					// Time conversion (ms) and add to PTN data array
					xt::xarray<float> timeInfoArray = xt::arange(0, int(modifiedLength / 8)) * TIMEGAIN;
					timeInfoArray.reshape({ -1, 1 });
					xt::xarray<float> ptnDataArrayWithTime = xt::hstack(xtuple(timeInfoArray, ptnDataArray));

					// X, Y Position conversion (mm)
					auto ptnPositionXView = xt::view(ptnDataArrayWithTime, xt::all(), xt::range(1, 2));
					auto ptnPositionYView = xt::view(ptnDataArrayWithTime, xt::all(), xt::range(2, 3));
					ptnPositionXView = (ptnPositionXView - XPOSOFFSET) * XPOSGAIN;
					ptnPositionYView = (ptnPositionYView - YPOSOFFSET) * YPOSGAIN;

					// X, Y Size conversion (mm)
					auto ptnSizeXView = xt::view(ptnDataArrayWithTime, xt::all(), xt::range(3, 4));
					auto ptnSizeYView = xt::view(ptnDataArrayWithTime, xt::all(), xt::range(4, 5));
					ptnSizeXView = ptnSizeXView * XPOSGAIN;
					ptnSizeYView = ptnSizeYView * YPOSGAIN;

					// result = (Time[ms], X[mm], Y[mm], X size[mm], Y size[mm], Dose 1[a.u.], Dose 2[a.u.], layer number, Beam On / Off)
					ptnDataSet.push_back(ptnDataArrayWithTime);
				}
				else std::cout << "System failed to open path :" << ptnFilePathList[i] << std::endl;
				inputLogFilePTN.close();
			}
			logFileLoaded = true;
			logFileLoading = false;
		}
	}
	return;
}

// Load excel dose monitor range file
void doseMonitorRangeFileThread()
{
	OpenXLSX::XLDocument doc;
	doc.open(doseMonitorRangeFileFullPath);

	auto workSheet = doc.workbook().worksheet("Sheet1");
	try 
	{
		for (int i = 1; i <= ptnFileNameList.size(); i++)
		{
			currentLogMonitorRange[i - 1] = workSheet.cell(OpenXLSX::XLCellReference("T" + std::to_string(i))).value().get<int64_t>();
		}
		try 
		{
			int overflow{};
			overflow = workSheet.cell(OpenXLSX::XLCellReference("T" + std::to_string(int(ptnFileNameList.size() + 1)))).value().get<int64_t>();
			if (overflow != 0)
			{
				doseMonitorRangeFileLoading = false;
				doseMonitorRangeFileLengthNotFit = true;
				return;
			}
		} 
		catch (OpenXLSX::XLException e) {}
	}
	catch (OpenXLSX::XLException e)
	{
		doseMonitorRangeFileLoading = false;
		doseMonitorRangeFileLengthNotFit = true;
		return;
	}
	
	doc.close();

	doseMonitorRangeFileSettingWindow = true;
	doseMonitorRangeFileLoading = false;
	return;
}

// Log file information saving as excel format
void logFileExcelSaveThread()
{
	if (savePtnAsExcel)
	{
		// Make excel file name
		std::string logFileName = ptnFileNameList[ptnSelected];
		logFileName.erase(logFileName.end() - 4, logFileName.end());
		logFileName = logFileName + "_ptn.xlsx";

		OpenXLSX::XLDocument doc;
		doc.create(logFileName);

		auto workSheet = doc.workbook().worksheet("Sheet1");

		workSheet.cell("A1").value() = "Time (ms)";
		workSheet.cell("B1").value() = "X Position";
		workSheet.cell("C1").value() = "Y Position";
		workSheet.cell("D1").value() = "MU count";

		for (int i = 0; i < ptnTimeDataVector.size(); i++)
		{
			workSheet.cell("A" + std::to_string(i + 2)).value().set<float>(ptnTimeDataVector[i]);
			workSheet.cell("B" + std::to_string(i + 2)).value().set<float>(ptnXDataVector[i]);
			workSheet.cell("C" + std::to_string(i + 2)).value().set<float>(ptnYDataVector[i]);
			workSheet.cell("D" + std::to_string(i + 2)).value().set<int>(ptnDoseMonitorDataVector[i]);
		}

		doc.save();
		doc.close();
		logFileExcelSaving = false;
		savePtnAsExcel = false;
	}
	else if (saveMgnAsExcel)
	{
		// Make excel file name
		std::string logFileName = mgnFileNameList[ptnSelected];
		logFileName.erase(logFileName.end() - 4, logFileName.end());
		logFileName = logFileName + "_mgn.xlsx";

		OpenXLSX::XLDocument doc;
		doc.create(logFileName);

		auto workSheet = doc.workbook().worksheet("Sheet1");

		workSheet.cell("A1").value() = "Segment number";
		workSheet.cell("B1").value() = "Time (ms)";
		workSheet.cell("C1").value() = "X Position";
		workSheet.cell("D1").value() = "Y Position";

		for (int i = 0; i < mgnTimeDataVector.size(); i++)
		{
			workSheet.cell("A" + std::to_string(i + 2)).value().set<int>(i+1);
			workSheet.cell("B" + std::to_string(i + 2)).value().set<float>(mgnTimeDataVector[i]);
			workSheet.cell("C" + std::to_string(i + 2)).value().set<float>(mgnXDataVector[i]);
			workSheet.cell("D" + std::to_string(i + 2)).value().set<float>(mgnYDataVector[i]);
		}

		doc.save();
		doc.close();
		logFileExcelSaving = false;
		saveMgnAsExcel = false;
	}
	
	return;
}

// Log file line segment division saving
void logFileDivSaveThread() 
{
	std::filesystem::path layerFolder("./" + ptnFileNameList[ptnSelected] + "_linesegment");
	std::filesystem::create_directory(layerFolder);

	for (int i = 0; i < mgnTimeDataVector.size() - 2; i++)
	{
		float segmentStart = mgnTimeDataVector[i + 1];
		float segmentEnd = mgnTimeDataVector[i + 2];

		auto selectedLogTimeView = xt::view(ptnDataSet[ptnSelected], xt::all(), xt::range(0, 1));
		xt::xarray<float> selectedLogTimeArray(selectedLogTimeView);
		auto segIndex = xt::ravel_indices(xt::argwhere(selectedLogTimeArray >= segmentStart && selectedLogTimeArray < segmentEnd), selectedLogTimeArray.shape());
		int segStartIndex = int(segIndex[0]);
		int segEndIndex = int(segIndex[int(segIndex.size()) - 1]);

		// Create views for selecting array and re-value for making log files
		auto selectedPtnView = xt::view(ptnDataSet[ptnSelected], xt::range(segStartIndex, segEndIndex + 1), xt::range(1, 9));
		xt::xarray<float> selectedPtnLineSegment(selectedPtnView);
		auto positionXView = xt::view(selectedPtnLineSegment, xt::all(), xt::range(0, 1));
		auto positionYView = xt::view(selectedPtnLineSegment, xt::all(), xt::range(1, 2));
		auto sizeXView = xt::view(selectedPtnLineSegment, xt::all(), xt::range(2, 3));
		auto sizeYView = xt::view(selectedPtnLineSegment, xt::all(), xt::range(3, 4));
		positionXView = (positionXView / XPOSGAIN) + XPOSOFFSET;
		positionYView = (positionYView / YPOSGAIN) + YPOSOFFSET;
		sizeXView = sizeXView / XPOSGAIN;
		sizeYView = sizeYView / YPOSGAIN;

		// Make line segment irradiation info flatten, and ready for unsigned short converison
		auto flattenSegmentView = xt::flatten(selectedPtnLineSegment);
		xt::xarray<float>selectedPtnLineSegmentFlat(flattenSegmentView);
		int segementLogFileSize = int(selectedPtnLineSegmentFlat.size());

		// Save information as individual log files
		std::string ptnLineSegmentFilePath = "./" + ptnFileNameList[ptnSelected] + "_linesegment/" + ptnFileNameList[ptnSelected] + "_linesegment" + std::to_string(i + 1) + ".ptn";
		std::ofstream outputFileStream(ptnLineSegmentFilePath, std::ifstream::binary);
	
		if (outputFileStream.is_open())
		{
			for (int i = 0; i < segementLogFileSize; i++)
			{
				unsigned short component = htons(int(selectedPtnLineSegmentFlat[i]));
				outputFileStream.write(reinterpret_cast<char*>(&component), sizeof(component));
			}
			outputFileStream.close();
		}
	}

	logFileDivSaving = false;
	return;
}

// TOPAS code generation function
void TOPASThread()
{
	if (TOPASCodeGenerating)
	{
		// Progress bar popup start
		TOPASCodeGenerationProgress = 0.0f;
		TOPASCodeGenerateStarted = true;
		std::error_code error;

		/* 1. Interpolate parameters */

		// 1.1.1 Beam spot size interpolation
		// Using piecewise cubic hermite interpolating polynomial, PCHIP method
		std::vector<double> protonEnergySigmaX{ 70, 100, 150, 162, 174, 182, 190, 206, 230 };
		std::vector<double> protonEnergySigmaY{ 70, 100, 150, 162, 174, 182, 190, 206, 230 };
		std::vector<double> protonEnergySigmaXPrime{ 70, 100, 150, 162, 174, 182, 190, 206, 230 };
		std::vector<double> protonEnergySigmaYPrime{ 70, 100, 150, 162, 174, 182, 190, 206, 230 };
		std::vector<double> spotCrossline{ 7.0, 5.1, 4.1, 3.8, 1.4, 1.0, 1.0, 0.94, 2 }; // SigmaX 
		std::vector<double> spotInline{ 7.6, 6.0, 4.4, 3.9, 1.4, 1.0, 0.9, 1.05, 2 }; // SigmaY
		std::vector<double> angularCrossline{ 0.0043, 0.0032, 0.0024, 0.0023, 0.0015, 0.0014, 0.0014, 0.0013, 0.00125 }; // SigmaX prime 
		std::vector<double> angularInline{ 0.0043, 0.0032, 0.0024, 0.0023, 0.0015, 0.0014, 0.0014, 0.0013, 0.00125 }; // SigmaY prime

		using boost::math::interpolators::pchip;
		auto sigmaXFitResult = pchip(std::move(protonEnergySigmaX), std::move(spotCrossline));
		auto sigmaYFitResult = pchip(std::move(protonEnergySigmaY), std::move(spotInline));
		auto sigmaXPrimeFitResult = pchip(std::move(protonEnergySigmaXPrime), std::move(angularCrossline));
		auto sigmaYPrimeFitResult = pchip(std::move(protonEnergySigmaYPrime), std::move(angularInline));

		// 1.1.2 Get spread value with gaussian curve with nonlinear least square from MATLAB (energy spread)
		// Gaussian model fitting, y = a * std::exp(-std::pow(((x - b)/c),2));
		// a(amplitude) = 0.7224, b(center) = 82.75, c(width) = 168.5

		// 1.1.3 Take result to container
		std::vector<std::vector<double>> sigmaXContainer;
		std::vector<std::vector<double>> sigmaYContainer;
		std::vector<std::vector<double>> sigmaXPrimeContainer;
		std::vector<std::vector<double>> sigmaYPrimeContainer;
		std::vector<std::vector<double>> energySpreadContainer;

		for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
		{
			std::vector<double> temporalSigmaX;
			std::vector<double> temporalSigmaY;
			std::vector<double> temporalSigmaXPrime;
			std::vector<double> temporalSigmaYPrime;
			std::vector<double> temporalEnergySpread;

			for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
			{
				temporalSigmaX.push_back(sigmaXFitResult(RTPlanEnergyLayer[i][j]));
				temporalSigmaY.push_back(sigmaYFitResult(RTPlanEnergyLayer[i][j]));
				temporalSigmaXPrime.push_back(sigmaXPrimeFitResult(RTPlanEnergyLayer[i][j]));
				temporalSigmaYPrime.push_back(sigmaYPrimeFitResult(RTPlanEnergyLayer[i][j]));
				temporalEnergySpread.push_back(gaussianFunc(RTPlanEnergyLayer[i][j]));
			}

			sigmaXContainer.push_back(temporalSigmaX);
			sigmaYContainer.push_back(temporalSigmaY);
			sigmaXPrimeContainer.push_back(temporalSigmaXPrime);
			sigmaYPrimeContainer.push_back(temporalSigmaYPrime);
			energySpreadContainer.push_back(temporalEnergySpread);
		}

		// 1.1 over, Increase progress 10%
		TOPASCodeGenerationProgress += 0.1f;

		// 1.2 Dipole magnet parameter interpolation

		// 2 dimension vector info of X, Y
		// [0] => energy layer (70, 100 , 150, 190, 230)
		// [1] => -250 ~ 250 coordinate (interval 0.1)
		// [2] => TOPAS dipole magnet tesla value

		std::vector<std::vector<double>> TOPASXTeslaInitial(3, std::vector<double>(25000, 0));
		std::vector<std::vector<double>> TOPASYTeslaInitial(3, std::vector<double>(25000, 0));

		// 1.2.1 Set overlapped information
		std::vector<double> XPosition;
		std::vector<double> YPosition;
		std::vector<std::vector<double>> posEnergyRange(5);

		for (double i = -250; i <= 250; i += 0.1)
		{
			XPosition.push_back(i); YPosition.push_back(i);
			posEnergyRange[0].push_back(70); posEnergyRange[1].push_back(100); posEnergyRange[2].push_back(150); posEnergyRange[3].push_back(190); posEnergyRange[4].push_back(230);
		}

		// 1.2.2 Set TOPAS tesla value for X,Y position
		// TOPAS_Tesla_X [0] = X_70, [1] = X_100, [2] = X_150, [3] = X_190, [4] = X_230
		// TOPAS_Tesla_Y [0] = Y_70, [1] = Y_100, [2] = Y_150, [3] = Y_190, [4] = Y_230
		std::vector<std::vector<double>> TOPAS_Tesla_X(5);
		std::vector<std::vector<double>> TOPAS_Tesla_Y(5);

		for (int i = 0; i <= 5000; i++)
		{
			TOPAS_Tesla_X[0].push_back(0.002355 * XPosition[i] - 0.0004194); // 70 MeV
			TOPAS_Tesla_X[1].push_back(0.002833 * XPosition[i] + 0.000004815); // 100 MeV
			TOPAS_Tesla_X[2].push_back(0.003521 * XPosition[i] - 0.002142); // 150 MeV
			TOPAS_Tesla_X[3].push_back(0.003984 * XPosition[i] + 0.00002222); // 190 MeV
			TOPAS_Tesla_X[4].push_back(0.004423 * XPosition[i] - 0.002717); // 230 MeV 

			TOPAS_Tesla_Y[0].push_back(-0.001862 * YPosition[i] - 0.00001595); // 70 MeV
			TOPAS_Tesla_Y[1].push_back(-0.002262 * YPosition[i] + 0.0004443); // 100 MeV
			TOPAS_Tesla_Y[2].push_back(-0.002817 * YPosition[i] + 0.001138); // 150 MeV
			TOPAS_Tesla_Y[3].push_back(-0.003185 * YPosition[i] + 0.0006288); // 190 MeV
			TOPAS_Tesla_Y[4].push_back(-0.003558 * YPosition[i] + 0.001441); // 230 MeV
		}

		// 1.2.3 interpolation and take result to container XTeslaDataset, YTeslaDataset

		// Prepare data for interpolation
		for (int i = 0; i < 5; i++)
		{
			// TOPASYTeslaInitial[0] = energy, TOPASYTeslaInitial[1] = log position, TOPASYTeslaInitial[2] = tesla value
			std::copy(posEnergyRange[i].begin(), posEnergyRange[i].end(), TOPASXTeslaInitial[0].begin() + 5000 * i);
			std::copy(XPosition.begin(), XPosition.end(), TOPASXTeslaInitial[1].begin() + 5000 * i);
			std::copy(TOPAS_Tesla_X[i].begin(), TOPAS_Tesla_X[i].end(), TOPASXTeslaInitial[2].begin() + 5000 * i);

			std::copy(posEnergyRange[i].begin(), posEnergyRange[i].end(), TOPASYTeslaInitial[0].begin() + 5000 * i);
			std::copy(YPosition.begin(), YPosition.end(), TOPASYTeslaInitial[1].begin() + 5000 * i);
			std::copy(TOPAS_Tesla_Y[i].begin(), TOPAS_Tesla_Y[i].end(), TOPASYTeslaInitial[2].begin() + 5000 * i);
		}

		// Energy layer information gathering
		std::vector<double> gatheredEnergyLayerInfo;
		for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
		{
			for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
			{
				gatheredEnergyLayerInfo.push_back(RTPlanEnergyLayer[i][j]);
			}
		}

		// Clear tesla dataset before interpolation and resize for current data
		XTeslaDataset.clear();
		YTeslaDataset.clear();
		XTeslaDataset.resize(ptnDataSet.size());
		YTeslaDataset.resize(ptnDataSet.size());

		// 2D linear interpolation for converting energy and log file position to tesla
		_2D::BicubicInterpolator<double> interp_X;
		_2D::BicubicInterpolator<double> interp_Y;
		interp_X.setData(TOPASXTeslaInitial[0], TOPASXTeslaInitial[1], TOPASXTeslaInitial[2]);
		interp_Y.setData(TOPASYTeslaInitial[0], TOPASYTeslaInitial[1], TOPASYTeslaInitial[2]);

		for (int i = 0; i < ptnDataSet.size(); i++)
		{
			auto ptnXPositionView = xt::view(ptnDataSet[i], xt::all(), xt::range(1, 2));
			auto ptnYPositionView = xt::view(ptnDataSet[i], xt::all(), xt::range(2, 3));
			xt::xarray<double> ptnXPositionXArray(ptnXPositionView);
			xt::xarray<double> ptnYPositionXArray(ptnYPositionView);
			std::vector<double> ptnXPositionTempVector(ptnXPositionXArray.begin(), ptnXPositionXArray.end());
			std::vector<double> ptnYPositionTempVector(ptnYPositionXArray.begin(), ptnYPositionXArray.end());
			int positionDataSize = int(ptnXPositionView.size());

			double currentBeamEnergy = gatheredEnergyLayerInfo[i];

			for (int j = 0; j < positionDataSize; j++)
			{
				XTeslaDataset[i].push_back(interp_X(currentBeamEnergy, ptnXPositionTempVector[j]));
				YTeslaDataset[i].push_back(interp_Y(currentBeamEnergy, ptnYPositionTempVector[j]));
			}
		}

		// Increase progress bar 10 %
		TOPASCodeGenerationProgress += 0.1f;

		// 1.3 MU correction with energy range and dose monitor range

		// Proton / Dose Correction
		std::vector<double> protonPerDoseEnergyRange = { 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230 };
		std::vector<double> protonPerDoseCorrectionFactor = { 1, 1.12573609032495, 1.25147616113001, 1.36888442326936, 1.48668286253201, 1.60497205195899, 1.71741194754422, 1.82898327045955, 1.94071715123743, 2.04829230739643, 2.16168786761159, 2.27629228444253, 2.39246901674031, 2.50561983301185, 2.63593473689952, 2.75663921459094, 2.89392497566575 };
		auto protonPerDoseCorrection = pchip(std::move(protonPerDoseEnergyRange), std::move(protonPerDoseCorrectionFactor));

		// Dose / MU Correction
		std::vector<double> dosePerMUCountEnergyRange = { 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230 };
		std::vector<double> dosePerMUCountCorrectionFactor = { 1, 0.989255716854649, 0.973421729297953, 0.967281770613755, 0.958215625815887, 0.946937840980162, 0.942685675037711, 0.940168906626851, 0.931161417057087, 0.918762676945622, 0.904569498824145, 0.888164591949398, 0.876689052268837, 0.872826195199581, 0.871540965585644, 0.859481169160383, 0.8524232713089 };
		
		auto dosePerMUCountCorrection = pchip(std::move(dosePerMUCountEnergyRange), std::move(dosePerMUCountCorrectionFactor));

		// 1.3 Over, Increase progress 10%, overall preprocess have 30%
		TOPASCodeGenerationProgress += 0.1f;

		/* 2. Generate folder and files */

		// Make a folder with patient ID
		std::filesystem::path targetFolderPath("./" + RTPlanPatientID);

		if (std::filesystem::exists(targetFolderPath)) // If file already exists, show the error
		{
			TOPASCodeGenerationProgress = 0.0f;
			TOPASCodeGenerating = false;
			folderAlreadyExists = true;
		}
		else
		{
			// Copy all topas base codes to target folder
			std::filesystem::path topasBaseCodeFolderPath("./topas_base_code");
			std::filesystem::path topasBaseCodeFile1Path("./topas_base_code/Loop_PretreatmentQA.txt");
			std::filesystem::path topasBaseCodeFile2Path("./topas_base_code/SMC_PBN_Nozzle_1.txt");
			std::filesystem::path topasBaseCodeFile3Path("./topas_base_code/SMC_PBN_Nozzle_2.txt");

			if (std::filesystem::exists(topasBaseCodeFolderPath) && std::filesystem::exists(topasBaseCodeFile1Path) && std::filesystem::exists(topasBaseCodeFile2Path) && std::filesystem::exists(topasBaseCodeFile3Path))
			{
				std::filesystem::create_directory(targetFolderPath);

				// Make separated energy layer code folder
				for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
				{
					std::filesystem::path fieldFolder("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1));
					std::filesystem::create_directory(fieldFolder);

					// Make bash file for auto run
					std::filesystem::path runbash("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/run.sh");
					std::ofstream runsh(runbash);

					runsh << "StartTime=$(date '+%Y-%m-%d %H:%M:%S')" << std::endl;

					for (int s = 1; s <= RTPlanEnergyLayer[i].size(); s++)
					{
						float RTPlanEnergyLayerFloat = round(RTPlanEnergyLayer[i][s-1] * 100) / 100;
						std::stringstream sstream; sstream << RTPlanEnergyLayerFloat;
						std::string RTPlanEnergyLayerString = sstream.str();

						runsh << "cd " << std::to_string(s) + "-" + RTPlanEnergyLayerString << std::endl;
						runsh << "echo $?" << std::endl;
						runsh << "topas Loop_PretreatmentQA.txt" << std::endl;
						runsh << "cd .." << std::endl;
					}

					runsh << "EndTime=$(date '+%Y-%m-%d %H:%M:%S')" << std::endl;
					runsh << "echo \"Start Time : \" $StartTime" << std::endl;
					runsh << "echo \"End Time : \" $EndTime" << std::endl;
					runsh.close();

					// Copy TOPAS basic code
					for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
					{
						float RTPlanEnergyLayerFloat = round(RTPlanEnergyLayer[i][j] * 100) / 100;
						std::stringstream sstream; sstream << RTPlanEnergyLayerFloat;
						std::string RTPlanEnergyLayerString = sstream.str();
						
						std::filesystem::path layerFolder("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString);
						std::filesystem::create_directory(layerFolder);

						// Copy Loop_PretreatmentQA.txt to each layer folder
						std::filesystem::copy(topasBaseCodeFile1Path, layerFolder, error);

						// Copy PBN_Nozzle.txt to each layer folder and add "includeFile  = ControlNozzle_(i).txt" to PBN_Nozzle.txt
						std::ofstream PBNNozzleText;
						std::string str = "includeFile  = ControlNozzle_" + std::to_string(j + 1) + ".txt";

						if (j < 9)
						{
							std::string currentFileName = "./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString +  "/SMC_PBN_Nozzle_1.txt";
							std::string changedFileName = "./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString + "/SMC_PBN_Nozzle.txt";
							std::filesystem::path currentFileNamePath(currentFileName);
							std::filesystem::path changedFileNamePath(changedFileName);
							std::filesystem::copy(topasBaseCodeFile2Path, layerFolder, error);
							PBNNozzleText.open(currentFileName, std::ios::out | std::ios::in);
							PBNNozzleText << str << std::endl;
							PBNNozzleText.close();
							std::filesystem::rename(currentFileNamePath, changedFileNamePath);
						}
						else
						{
							std::string currentFileName = "./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString + "/SMC_PBN_Nozzle_2.txt";
							std::string changedFileName = "./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString + "/SMC_PBN_Nozzle.txt";
							std::filesystem::path currentFileNamePath(currentFileName);
							std::filesystem::path changedFileNamePath(changedFileName);
							std::filesystem::copy(topasBaseCodeFile3Path, layerFolder, error);
							PBNNozzleText.open(currentFileName, std::ios::out | std::ios::in);
							PBNNozzleText << str << std::endl;
							PBNNozzleText.close();
							std::filesystem::rename(currentFileNamePath, changedFileNamePath);
						}

						// Make ControlNozzle(i).txt file
						std::ofstream controlNozzleText;
						controlNozzleText.open("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString + "/ControlNozzle_" + std::to_string(j + 1) + ".txt");

						// Get time and MU information from PTN dataset
						int ptnTimeSize{ 0 };
						int currentOffset{ 0 };
						std::vector<float> timeInfo;
						std::vector<float> particleCountInfo;

						// Dose monitor range correction factor
						double monitorRangeFactor{ 1.0 };

						if (i != 0) { for (int k = 0; k < i; k++) currentOffset += int(RTPlanEnergyLayer[k].size()); }

						auto ptnTimeView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(0, 1));
						ptnTimeSize = int(ptnTimeView.size());
						xt::xarray<float> tempXarray(ptnTimeView);
						std::vector<float> tempTimeVector(tempXarray.begin(), tempXarray.end());
						timeInfo.resize(ptnTimeSize);
						std::copy(tempTimeVector.begin(), tempTimeVector.end(), timeInfo.begin());

						if (currentLogMonitorRange[currentOffset + j] == 2) monitorRangeFactor = 1.0;
						else if (currentLogMonitorRange[currentOffset + j] == 3) monitorRangeFactor = 2.978723404255319;
						else if (currentLogMonitorRange[currentOffset + j] == 4) monitorRangeFactor = 8.936170212765957;
						else if (currentLogMonitorRange[currentOffset + j] == 5) monitorRangeFactor = 26.80851063829787;

						auto ptnMUInfoView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(5, 6));
						xt::xarray<float> ptnMUInfo(ptnMUInfoView);

						if (setForCalibration)
						{
							if (useCorrectionFactorForCalibration)
							{
								ptnMUInfo = ptnMUInfo * protonPerDoseCorrection(RTPlanEnergyLayer[i][j]);
								ptnMUInfo = ptnMUInfo * dosePerMUCountCorrection(RTPlanEnergyLayer[i][j]);
							}
							ptnMUInfo = ptnMUInfo * monitorRangeFactor;
							ptnMUInfo = ptnMUInfo / doseDividingFactor;
						}
						else
						{
							ptnMUInfo = ptnMUInfo * protonPerDoseCorrection(RTPlanEnergyLayer[i][j]);
							ptnMUInfo = ptnMUInfo * dosePerMUCountCorrection(RTPlanEnergyLayer[i][j]);
							ptnMUInfo = ptnMUInfo * monitorRangeFactor;
							ptnMUInfo = ptnMUInfo / doseDividingFactor;
						}
				
						xt::xarray<float> tempPtnMUInfo(ptnMUInfo);
						std::vector<float> tempMUVector(tempPtnMUInfo.begin(), tempPtnMUInfo.end());
						particleCountInfo.resize(ptnMUInfo.size());
						std::copy(tempMUVector.begin(), tempMUVector.end(), particleCountInfo.begin());

						// Data transfer to result vector
						particleCountResult.push_back(particleCountInfo);

						if (useHUtoMaterialSchneider) controlNozzleText << "IncludeFile = HUtoMaterialSchneider.txt" << std::endl << std::endl;

						controlNozzleText << "## Beam parameters ##" << std::endl << std::endl;
						controlNozzleText << "d:So/MyBeam/BeamEnergy = " << RTPlanEnergyLayer[i][j] << " MeV" << std::endl;
						controlNozzleText << "u:So/MyBeam/BeamEnergySpread = " << energySpreadContainer[i][j] << std::endl;
						controlNozzleText << "d:So/MyBeam/SigmaX = " << sigmaXContainer[i][j] << " mm" << std::endl;
						controlNozzleText << "u:So/MyBeam/SigmaXprime = " << sigmaXPrimeContainer[i][j] << std::endl;
						controlNozzleText << "d:So/MyBeam/SigmaY = " << sigmaYContainer[i][j] << " mm" << std::endl;
						controlNozzleText << "u:So/MyBeam/SigmaYprime = " << sigmaYPrimeContainer[i][j] << std::endl << std::endl;

						// If one of beam has degrader sequence, write degrader information 
						if (RTPlanDegraderList[i] == "Degrader")
						{
							controlNozzleText << "## Range Shifter ##" << std::endl << std::endl;
							controlNozzleText << "s:Ge/RangeShift/Type = \"TsBox\"" << std::endl;
							controlNozzleText << "s:Ge/RangeShift/Parent = \"Phantom\"" << std::endl;
							controlNozzleText << "s:Ge/RangeShift/Material = \"water\"" << std::endl;
							controlNozzleText << "d:Ge/RangeShift/HLX = 200. mm" << std::endl;
							controlNozzleText << "d:Ge/RangeShift/HLY = 200. mm" << std::endl;
							controlNozzleText << "d:Ge/RangeShift/HLZ = 20. mm" << std::endl;
							controlNozzleText << "d:Ge/RangeShift/TransZ = " << std::round(RTPlanSnoutPosition[i] + 20) << ". mm" << std::endl << std::endl;
						}

						controlNozzleText << "## Dipole magnet control ##" << std::endl << std::endl;
						controlNozzleText << "s:Tf/Dipolemagnet1st/Function = \"step\"" << std::endl;
						controlNozzleText << "dv:Tf/Dipolemagnet1st/Times = " << ptnTimeSize << std::endl;
						for (int k = 0; k < timeInfo.size(); k++) controlNozzleText << std::to_string(timeInfo[k]) + " ";
						controlNozzleText << "ms" << std::endl;
						controlNozzleText << "dv:Tf/Dipolemagnet1st/values = " << ptnTimeSize << std::endl;
						for (int k = 0; k < XTeslaDataset[currentOffset + j].size(); k++) controlNozzleText << std::to_string(XTeslaDataset[currentOffset + j][k]) + " ";
						controlNozzleText << "tesla" << std::endl;
						controlNozzleText << "s:Tf/Dipolemagnet2nd/Function = \"step\"" << std::endl;
						controlNozzleText << "dv:Tf/Dipolemagnet2nd/Times = " << ptnTimeSize << std::endl;
						for (int k = 0; k < timeInfo.size(); k++) controlNozzleText << std::to_string(timeInfo[k]) + " ";
						controlNozzleText << "ms" << std::endl;
						controlNozzleText << "dv:Tf/Dipolemagnet2nd/values = " << ptnTimeSize << std::endl;
						for (int k = 0; k < YTeslaDataset[currentOffset + j].size(); k++) controlNozzleText << std::to_string(YTeslaDataset[currentOffset + j][k]) + " ";
						controlNozzleText << "tesla" << std::endl << std::endl;
						controlNozzleText << "d:Tf/TimelineEnd = " << timeInfo.back() << " ms" << std::endl;
						controlNozzleText << "i:Tf/NumberofsequentialTimes = " << ptnTimeSize << std::endl << std::endl;

						controlNozzleText << "## Particle Weight ## " << std::endl << std::endl;
						controlNozzleText << "s:Tf/Particles/Function = \"step\"" << std::endl;
						controlNozzleText << "dv:Tf/Particles/Times = " << ptnTimeSize << std::endl;
						for (int k = 0; k < timeInfo.size(); k++) controlNozzleText << std::to_string(timeInfo[k]) + " ";
						controlNozzleText << "ms" << std::endl;
						controlNozzleText << "iv:Tf/Particles/values = " << ptnTimeSize << std::endl;
						for (int k = 0; k < particleCountInfo.size(); k++) controlNozzleText << std::to_string(int(std::round(particleCountInfo[k]))) + " ";
						controlNozzleText.close();
					}
					// Increase the progress with one field generation done 
					TOPASCodeGenerationProgress += 0.7f * (1 / float(RTPlanNumberOfBeams));
				}
			}
			else
			{
				TOPASCodeGenerating = false;
				TOPASBaseCodeNotExist = true;
			}
			TOPASCodeGenerated = true;
			TOPASCodeGenerating = false;
		}
	}
	return;
}

void MOQUIThread()
{
	if (MOQUICodeGenerating)
	{
		MOQUICodeGenerateStarted = true;
		MOQUICodeGenerationProgress = 0.0f;

		// MU correction with energy range and dose monitor range
		using boost::math::interpolators::pchip;
		// Proton / Dose Correction
		std::vector<double> protonPerDoseEnergyRange = { 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230 };
		std::vector<double> protonPerDoseCorrectionFactor = { 1, 1.12573609032495, 1.25147616113001, 1.36888442326936, 1.48668286253201, 1.60497205195899, 1.71741194754422, 1.82898327045955, 1.94071715123743, 2.04829230739643, 2.16168786761159, 2.27629228444253, 2.39246901674031, 2.50561983301185, 2.63593473689952, 2.75663921459094, 2.89392497566575 };
		auto protonPerDoseCorrection = pchip(std::move(protonPerDoseEnergyRange), std::move(protonPerDoseCorrectionFactor));

		// Dose / MU Correction
		std::vector<double> dosePerMUCountEnergyRange = { 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230 };
		std::vector<double> dosePerMUCountCorrectionFactor = { 1, 0.989255716854649, 0.973421729297953, 0.967281770613755, 0.958215625815887, 0.946937840980162, 0.942685675037711, 0.940168906626851, 0.931161417057087, 0.918762676945622, 0.904569498824145, 0.888164591949398, 0.876689052268837, 0.872826195199581, 0.871540965585644, 0.859481169160383, 0.8524232713089 };
		auto dosePerMUCountCorrection = pchip(std::move(dosePerMUCountEnergyRange), std::move(dosePerMUCountCorrectionFactor));

		MOQUICodeGenerationProgress = 0.3f;

		// Make a folder with patient ID
		std::filesystem::path targetFolderPath("./" + RTPlanPatientID);
	
		if (std::filesystem::exists(targetFolderPath)) // If file already exists, show the error
		{
			MOQUICodeGenerationProgress = 0.0f;
			MOQUICodeGenerating = false;
			folderAlreadyExists = true;
		}
		else
		{
			std::filesystem::create_directory(targetFolderPath);

			// Make separated energy layer code folder
			for (int i = 0; i < RTPlanEnergyLayer.size(); i++)
			{
				std::filesystem::path fieldFolder("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1));
				std::filesystem::create_directory(fieldFolder);

				// Copy TOPAS basic code
				for (int j = 0; j < RTPlanEnergyLayer[i].size(); j++)
				{
					float RTPlanEnergyLayerFloat = round(RTPlanEnergyLayer[i][j] * 100) / 100;
					std::stringstream sstream; sstream << RTPlanEnergyLayerFloat;
					std::string RTPlanEnergyLayerString = sstream.str();

					//std::filesystem::path layerFolder("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + std::to_string(j + 1) + "-" + RTPlanEnergyLayerString);
					//std::filesystem::create_directory(layerFolder);

					// Get time and MU information from PTN dataset
					int ptnTimeSize{ 0 };
					int currentOffset{ 0 };
					std::vector<float> timeInfo;
					std::vector<float> particleCountInfo;

					// Dose monitor range correction factor
					double monitorRangeFactor{ 1.0 };

					if (i != 0) { for (int k = 0; k < i; k++) currentOffset += int(RTPlanEnergyLayer[k].size()); }

					auto ptnTimeView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(0, 1));
					ptnTimeSize = int(ptnTimeView.size());
					xt::xarray<float> tempXarray(ptnTimeView);
					std::vector<float> tempTimeVector(tempXarray.begin(), tempXarray.end());
					timeInfo.resize(ptnTimeSize);
					std::copy(tempTimeVector.begin(), tempTimeVector.end(), timeInfo.begin());

					if (currentLogMonitorRange[currentOffset + j] == 2) monitorRangeFactor = 1.0;
					else if (currentLogMonitorRange[currentOffset + j] == 3) monitorRangeFactor = 2.978723404255319;
					else if (currentLogMonitorRange[currentOffset + j] == 4) monitorRangeFactor = 8.936170212765957;
					else if (currentLogMonitorRange[currentOffset + j] == 5) monitorRangeFactor = 26.80851063829787;

					auto ptnMUInfoView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(5, 6));
					xt::xarray<float> ptnMUInfo(ptnMUInfoView);

					// Correction for monitor range and dividing factor
					ptnMUInfo = ptnMUInfo * monitorRangeFactor;
					ptnMUInfo = ptnMUInfo / doseDividingFactor;

					xt::xarray<float> tempPtnMUInfo(ptnMUInfo);
					std::vector<float> tempMUVector(tempPtnMUInfo.begin(), tempPtnMUInfo.end());
					particleCountInfo.resize(ptnMUInfo.size());
					std::copy(tempMUVector.begin(), tempMUVector.end(), particleCountInfo.begin());

					// Data transfer to result vector
					particleCountResult.push_back(particleCountInfo);

					// Create CSV file for each log files
					std::string additionalZero = "";
					if (j + 1 < 10) additionalZero = "0";
					std::string csvFileName = additionalZero + std::to_string(j + 1) + "_" + RTPlanEnergyLayerString + "MeV.csv";
					std::ofstream csvOutput("./" + RTPlanPatientID + "/Field" + std::to_string(i + 1) + "/" + csvFileName);

					auto currentPtnTimeView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(0, 1));
					auto currentPtnXPosView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(1, 2));
					auto currentPtnYPosView = xt::view(ptnDataSet[currentOffset + j], xt::all(), xt::range(2, 3));

					xt::xarray<float> ptnTimeInfoArray(currentPtnTimeView);
					xt::xarray<float> ptnXPosInfoArray(currentPtnXPosView);
					xt::xarray<float> ptnYPosInfoArray(currentPtnYPosView);

					std::vector<float> ptnTimeDataContainer(ptnTimeInfoArray.begin(), ptnTimeInfoArray.end());
					std::vector<float> ptnXPosDataContainer(ptnXPosInfoArray.begin(), ptnXPosInfoArray.end());
					std::vector<float> ptnYPosDataContainer(ptnYPosInfoArray.begin(), ptnYPosInfoArray.end());

					for (int k = 0; k < ptnTimeDataContainer.size(); k++)
					{
						if (k < ptnTimeDataContainer.size() - 1) csvOutput << std::to_string(ptnTimeDataContainer[k]) << "," << std::to_string(ptnXPosDataContainer[k]) << "," << std::to_string(ptnYPosDataContainer[k]) << "," << std::round(particleCountInfo[k]) << ",";
						else csvOutput << std::to_string(ptnTimeDataContainer[k]) << "," << std::to_string(ptnXPosDataContainer[k]) << "," << std::to_string(ptnYPosDataContainer[k]) << "," << std::round(particleCountInfo[k]);
					}
				
					csvOutput.close();
				}
				// Increase the progress with one field generation done 
				TOPASCodeGenerationProgress += 0.7f * (1 / float(RTPlanNumberOfBeams));
			}
			MOQUICodeGenerating = false;
			MOQUICodeGenerated = true;
		}
	}
	else
	{
		MOQUICodeGenerating = false;
	}

	return;
}