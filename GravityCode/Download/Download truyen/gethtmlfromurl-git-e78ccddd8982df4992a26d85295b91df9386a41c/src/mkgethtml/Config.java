package mkgethtml;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;

import javax.swing.SwingUtilities;

import com.google.gson.JsonSyntaxException;

import common.CommonValue;
import common.Enumeration;
import common.Enumeration.ConfigType;
import common.Enumeration.EnumConfigKey;
import javafx.application.Platform;
import log.CommonLog;
import mk.constant.Constant;
import models.LoginInfo;
import models.PageConfig;
import utils.JSONUtil;
import utils.XMLParse;

public class Config {
	private static HashMap<Enumeration.EnumConfigKey, Object> configDataSetting = new HashMap<>();
	private static ArrayList<PageConfig> configHost = new ArrayList<>();
	private static ArrayList<LoginInfo> loginDataConfig = new ArrayList<>();
	private static Boolean isFirstLoad = true;

	/**
	 * add new host
	 * 
	 * @param p
	 */
	public static void addHost(PageConfig p) {
		configHost.add(p);
		saveConfig(ConfigType.DataSite);
	}

	/**
	 * delete host by pageCode
	 * 
	 * @param pageCode
	 */
	public static void deleteHostByPageCode(String pageCode) {
		if (configHost.contains(new PageConfig(pageCode))) {
			configHost.remove(new PageConfig(pageCode));
			saveConfig(ConfigType.DataSite);
		}
	}

	/**
	 * edit host
	 * 
	 * @param replace
	 * @param replacement
	 */
	public static void editHost(PageConfig replace, PageConfig replacement) {
		int indexOfPage = configHost.indexOf(replace);
		if (indexOfPage > -1) {
			configHost.set(indexOfPage, replacement);
			saveConfig(ConfigType.DataSite);
		}
	}

	/**
	 * get list from json
	 * 
	 * @return
	 */
	public static ArrayList<PageConfig> getAllHostConfig() {
		return configHost;
	}

	/**
	 * @param pageCode
	 *            - or hostname of fiction website
	 * @return PageConfig of site if have , NULL if not
	 */
	public static PageConfig getHostConfigByPageCode(String pageCode) {
		PageConfig p = new PageConfig(pageCode);
		if (configHost.contains(p)) {
			return configHost.get(configHost.indexOf(p));
		}
		return null;
	}

	/**
	 * Check url is support by app or not
	 * 
	 * @param url
	 * @return 1 if support 0 does not support and -1 using for manual only
	 */
	public static int isSupportHost(String url) {
		PageConfig check = new PageConfig(url.toLowerCase());
		for (PageConfig pageConfig : configHost) {
			if (check.equals(pageConfig)) {
				if (pageConfig.getIsManualGet()) {
					return -1;
				}
				return 1;
			}
		}
		return 0;
	}

	/**
	 * add/edit login host info
	 * 
	 * @param replace
	 * @param replacement
	 */
	public static void updateLoginInfo(LoginInfo loginInfo, String pageCode) {
		int indexOfLogin = loginDataConfig.indexOf(loginInfo);
		if (indexOfLogin > -1) {
			loginDataConfig.set(indexOfLogin, loginInfo);

		} else {
			loginDataConfig.add(loginInfo);
		}
		configDataSetting.put(EnumConfigKey.LOGIN_INFO, loginDataConfig);
		saveConfig(ConfigType.Setting);
	}

	/**
	 * get LoginInfo by pageCode
	 * 
	 * @param pageCode
	 */
	public static LoginInfo getLoginInfoByPageCode(String pageCode) {
		LoginInfo loginInfo = new LoginInfo(pageCode);
		if (loginDataConfig.contains(loginInfo)) {
			return loginDataConfig.get(loginDataConfig.indexOf(loginInfo));
		}
		return null;
	}

	/**
	 * init default config for user and hostconfig
	 * 
	 * @param isReconfig
	 *            - force create
	 */
	static void createDefaultConfig(Boolean isReconfig) {
		createDefaultHostConfig(isReconfig);
		createDefaultUserConfig(isReconfig);
	}

	/**
	 * create user default config
	 * 
	 * @param isReconfig
	 *            - force create
	 */
	static void createDefaultUserConfig(Boolean isReconfig) {
		HashMap<Enumeration.EnumConfigKey, Object> config = new HashMap<>();
		String configPath = getConfigPathByConfigType(ConfigType.Setting);

		try {
			File file = new File(configPath);

			config.put(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE);
			config.put(EnumConfigKey.RECENT_FOLDER, Constant.DEFAULT_RECENT_FOLDER);
			config.put(EnumConfigKey.LINE_HEIGHT, Constant.DEFAULT_LINE_HEIGH);
			config.put(EnumConfigKey.SLEEP_TIME, Constant.DEFAULT_SLEEP_TIME);
			config.put(EnumConfigKey.TIME_OUT, Constant.DEFAULT_TIME_OUT);
			config.put(EnumConfigKey.MAXCONNECTION, Constant.DEFAULT_MAX_CONNECTION);

			config.put(EnumConfigKey.EBOOKCREATOR, "mkbyme");
			config.put(EnumConfigKey.CONVERTER, "");
			config.put(EnumConfigKey.SOURCE, "");
			config.put(EnumConfigKey.AUTHOR, "");
			config.put(EnumConfigKey.EBOOKNAME, "");
			config.put(EnumConfigKey.STATUS, "");
			config.put(EnumConfigKey.INFO,
					String.format(
							"<br/>Được tạo bằng phần mềm: <a href =\"https://sourceforge.net/projects/gethtmlfromurl/\">%s</a>",
							CommonValue.getAppName()));
			config.put(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING);

			// 2 level of Table of content config
			config.put(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, false);
			config.put(EnumConfigKey.TWO_LEVEL_CHAPTER_TITLE, Constant.DEFAULT_TWO_LEVEL_CHAPTER_TITLE);
			config.put(EnumConfigKey.TWO_LEVEL_BREAK_CHAPTER_COUNT, Constant.DEFAULT_TWO_LEVEL_BREAK_CHAPTER_COUNT);

			// show link "View image 1" on chapter
			config.put(EnumConfigKey.IS_SHOW_PAGE_HAS_IMAGE, true);

			Boolean isSave = false;
			if (!file.exists()) {
				file.createNewFile();
				isSave = true;

			} else if (isReconfig) {
				isSave = true;
			}
			if (isSave) {
				XMLParse.saveConfig(configPath, config);
			}

		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/**
	 * default list host config
	 * 
	 * @param isReconfig
	 *            - force create
	 */
	static void createDefaultHostConfig(Boolean isReconfig) {
		String configPath = getConfigPathByConfigType(ConfigType.DataSite);
		try {
			File file = new File(configPath);

			ArrayList<PageConfig> listPageConfig = new ArrayList<>();
			PageConfig p = new PageConfig();

			p.setPageCode("truyenfull.vn");
			p.setIsVietNameseHost(true);
			p.setPagingPattern("trang-");
			p.setCssQueryGetListChapter("#list-chapter .row ul{start=0&end=n}");
			p.setCssQueryGetChapterTitle(".row .chapter-title");
			p.setCssQueryGetChapterContent(".row .chapter-c");
			p.setUrlPageTest("http://truyenfull.vn/dai-hoc-la-gi-inspired-by-a-true-story/");
			p.setOverMaxSizePageCountState(Enumeration.OverMaxSizePageCountState.MOVE_TO_LAST);
			String guide = "1. Truy cập trang http://truyenfull.vn\n" + "2. Chọn 1 truyện nhấn và mở đọc truyện\n"
					+ "3. Sao chép đường dẫn truyện ở thanh địa chỉ trình duyệt\n" + "4. Dán vào URL trên phần mềm\n\n"
					+ "Dạng URL:\n" + "http://truyenfull.vn/[TÊN_TRUYỆN]/\n" + "Ví dụ:\n"
					+ "http://truyenfull.vn/dai-hoc-la-gi-inspired-by-a-true-story/\n" + "là hợp lệ\n" + "------\n"
					+ "Nhấn Tải xuống.";
			p.setTextGuide(guide);
			listPageConfig.add(p);

			Boolean isSave = false;
			if (!file.exists()) {
				file.createNewFile();
				isSave = true;

			} else if (isReconfig) {
				isSave = true;
			}
			if (isSave) {
				try {
					JSONUtil.saveConfig(configPath, listPageConfig);
				} catch (FileNotFoundException e) {
					e.printStackTrace();
				}
			}

		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/**
	 * return Object from key of HashMap Config
	 * 
	 * @param key
	 * @return
	 */
	public static Object get(Enumeration.EnumConfigKey key) {
		loadConfig();
		return configDataSetting.get(key);
	}

	/**
	 * Default method need to call before using other methoad
	 * 
	 * @return
	 */
	public static void initConfig() {

		createDefaultConfig(false);

		loadConfig();

		CommonValue.initValue();
	}

	/**
	 * load config
	 */
	@SuppressWarnings("unchecked")
	private static void loadConfig() {
		// load userConfig
		if (configDataSetting.isEmpty()) {
			try {
				configDataSetting = (HashMap<Enumeration.EnumConfigKey, Object>) XMLParse
						.loadConfig(getConfigPathByConfigType(ConfigType.Setting));

				if (configDataSetting.isEmpty()) {
					// when crash try to create new one
					createDefaultUserConfig(true);
					configDataSetting = (HashMap<Enumeration.EnumConfigKey, Object>) XMLParse
							.loadConfig(getConfigPathByConfigType(ConfigType.Setting));
				}
			} catch (FileNotFoundException | NullPointerException | ClassNotFoundException | NoSuchMethodException e) {
				e.printStackTrace();
				CommonLog.logError(e);
			}

		} else if (isFirstLoad) {
			isFirstLoad = false;
			loginDataConfig = (ArrayList<LoginInfo>) configDataSetting.get(Enumeration.EnumConfigKey.LOGIN_INFO);
			if (loginDataConfig == null) {
				loginDataConfig = new ArrayList<>();
			}
		}
		// load list host
		if (configHost.isEmpty()) {
			try {
				configHost = JSONUtil.loadConfig(getConfigPathByConfigType(ConfigType.DataSite));
			} catch (FileNotFoundException e) {
				e.printStackTrace();
			} catch (JsonSyntaxException e) {
				// file host got error - reset
				try {
					createDefaultHostConfig(true);
					loadConfig();
				} catch (Exception e1) {
					e1.printStackTrace();
				}
			}
		}

	}

	/**
	 * put value to HashMap Config
	 * 
	 * @param key
	 * @param value
	 */
	public static void put(Enumeration.EnumConfigKey key, Object value) {
		if (Platform.isFxApplicationThread()) {
			SwingUtilities.invokeLater(new Runnable() {

				@Override
				public void run() {
					configDataSetting.put(key, value);
				}
			});
		} else {
			configDataSetting.put(key, value);
		}
	}

	/**
	 * put value to HashMap Config
	 * 
	 * @param key
	 * @param value
	 * @param isSave
	 *            - save after put value
	 */
	public static void put(Enumeration.EnumConfigKey key, Object value, Boolean isSave) {
		if (Platform.isFxApplicationThread()) {
			SwingUtilities.invokeLater(new Runnable() {

				@Override
				public void run() {
					configDataSetting.put(key, value);
					if (isSave) {
						saveConfig(Enumeration.ConfigType.Setting);
					}
				}
			});
		} else {
			configDataSetting.put(key, value);
			if (isSave) {
				saveConfig(Enumeration.ConfigType.Setting);
			}
		}
	}

	/**
	 * Recreate file Config struct if could not be loaded
	 */
	public static void reConfig() {
		createDefaultConfig(true);
		if (configDataSetting != null) {

			configDataSetting.clear();
		}
		if (loginDataConfig != null) {

			loginDataConfig.clear();
		}
		loadConfig();

	}

	/**
	 * return key from HashMap Config
	 * 
	 * @param key
	 */
	public static void remove(Enumeration.EnumConfigKey key) {
		if (configDataSetting != null) {
			configDataSetting.remove(key);
		}
	}

	/**
	 * Save config by config Type
	 * 
	 * @param configType
	 */
	public static void saveConfig(Enumeration.ConfigType configType) {
		String configPath = getConfigPathByConfigType(configType);
		File f = new File(configPath);

		try {
			if (!f.exists()) {
				f.createNewFile();
			}
			switch (configType) {
			case DataSite:
				JSONUtil.saveConfig(configPath, configHost);

				break;
			case Setting:
				XMLParse.saveConfig(configPath, configDataSetting);
				break;
			default:
				JSONUtil.saveConfig(configPath, configHost);
				break;
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/**
	 * get config path by configType
	 * 
	 * @param configType
	 * @return String
	 * 
	 */
	private static String getConfigPathByConfigType(Enumeration.ConfigType configType) {
		String ret = "";
		switch (configType) {
		case DataSite:
			ret = Constant.CONFIG_DATASITE_FILE;
			break;
		case Setting:
			ret = Constant.CONFIG_USER_SETTING_FILE;
			break;

		default:
			ret = Constant.CONFIG_DATASITE_FILE;
			break;
		}
		return ret;
	}
}
