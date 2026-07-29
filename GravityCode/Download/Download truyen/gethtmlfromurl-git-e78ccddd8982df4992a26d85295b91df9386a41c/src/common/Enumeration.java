/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package common;

/**
 *
 * @author Adminz
 */
public class Enumeration {

	/**
	 * @author nxcuo Enum get Config Key
	 */
	public enum EnumConfigKey {
		/// Language of app
		LANGUAGE,
		/// Line height
		LINE_HEIGHT,
		/// store all page config
		DATASITE,
		/// Ebook Info - Name
		EBOOKNAME,
		/// Ebook Info - Author
		AUTHOR,
		/// Ebook Info - Creator
		EBOOKCREATOR,
		/// Ebook Info - Info
		INFO,
		/// Ebook Info - Source
		SOURCE,
		/// Ebook Info - Status of ebook
		STATUS,
		/// Ebook Info - Converter's Name
		CONVERTER,
		/// Max connection to download
		MAXCONNECTION,
		/// Last folder
		RECENT_FOLDER,
		/// time to sleep between thread download
		SLEEP_TIME,
		/// time out to download
		TIME_OUT,
		/// after update will delete this file
		DELETE_ON_EXIST,
		/// app encoding
		ENCODING,
		/// truyencv userid to unblock
		TRUYENCVUSERID,
		/// browser loading image
		ISLOADIMAGE,
		// login info
		LOGIN_INFO,
		// checkbox chckbxOneFilePer
		REMEMBER_ONE_PER_FILE,

		// show tips when download failed
		SHOW_TIPS_ON_DOWNLOAD_FAILED,

		// use 2 level for table of content
		IS_USE_2_LEVEL_FOR_TOC,
		// 2 level TOC chapter title
		TWO_LEVEL_CHAPTER_TITLE,
		// 2 level break chapter count
		TWO_LEVEL_BREAK_CHAPTER_COUNT,

		// setting show "View image 1.." default true
		IS_SHOW_PAGE_HAS_IMAGE,

	}

	/**
	 * enum declare state of page when overload
	 * 
	 * @author nxcuo
	 *
	 */
	public enum OverMaxSizePageCountState {
		MOVE_TO_FIRST(1), MOVE_TO_LAST(2), MOVE_TO_PAGE_WITHOUT_CHAPTER_LIST(3);

		private int value;

		OverMaxSizePageCountState(int value) {
			this.value = value;
		}

		public int getInt() {
			return value;

		}

	}

	/**
	 * enum of update app or config state
	 * 
	 * @author nxcuo
	 *
	 */
	public enum UpdateState {

		/**
		 * Offline mode
		 */
		NoNetWorking(1),
		/**
		 * sourcefore is offline, this host use to check update
		 */
		GetAppUpdateInfoFailed(2),
		/**
		 * app version is obsolete
		 */
		AppOutOfUpdate(3),
		/**
		 * app is up to date
		 */
		AppUpdated(4),
		/**
		 * Config is obsolete
		 */
		ConfigOutOfUpdate(5),
		/**
		 * Config is up to date
		 */
		ConfigUpdated(6);
		private int value;

		UpdateState(int value) {
			this.value = value;
		}

		public int getInt() {
			return value;

		}
	}

	/**
	 * enum of save data type
	 * 
	 * @author nxcuo
	 *
	 */
	public enum ConfigType {

		/**
		 * list host config
		 */
		DataSite,
		/**
		 * User config(setting, UX)
		 */
		Setting,

	}

	/**
	 * Type of log
	 * 
	 * @author nxcuo
	 *
	 */
	public enum LogType {
		/**
		 * info log
		 */
		Info,
		/**
		 * error log
		 */
		Error,
		/**
		 * Warning log
		 */
		Warning
	}

	public enum UIType {
		/**
		 * log to main window
		 */
		MainWindow,
		/**
		 * log to page config manager window
		 */
		PageConfigWindow,
		/**
		 * Log to manual get UI
		 */
		ManualUIWindow
	}

	/**
	 * all type of enum config
	 * 
	 * @author nxcuo
	 *
	 */
	public enum ConfigDataType {
		Int, String, Boolean, Long, Object,
	}
}
