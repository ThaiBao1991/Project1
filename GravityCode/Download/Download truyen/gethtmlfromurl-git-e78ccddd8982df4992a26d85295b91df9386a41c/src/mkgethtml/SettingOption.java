package mkgethtml;

import common.Enumeration.EnumConfigKey;
import log.CommonLog;

/**
 * GET User setting option
 * 
 * @author nxcuo
 *
 */
public class SettingOption {
	private static int count = 0;
	private static Boolean isDebug = false;

	/**
	 * Get option setting return Bool
	 * 
	 * @param configKey
	 * @param defaultValue
	 * @return
	 * @author mkbyme Jan 27, 2019
	 */
	public static Boolean getBoolean(EnumConfigKey configKey, Boolean defaultValue) {
		Boolean optionValue = defaultValue;
		try {
			Object obj = Config.get(configKey);
			if (obj != null) {
				optionValue = Boolean.parseBoolean(obj.toString());
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ": Read not null:" + (++count));
				}
			} else {
				Config.put(configKey, optionValue, true);
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ": Read null + save:" + (++count));
				}
			}
		} catch (Exception e) {
			optionValue = defaultValue;
			e.printStackTrace();
			CommonLog.logError(e);
			Config.put(configKey, defaultValue, true);
			if (isDebug) {
				System.out.println(System.currentTimeMillis() + ": Read null + save + exception:" + (++count));
			}
		}
		return optionValue;
	}

	/**
	 * Get option setting return String
	 * 
	 * @param configKey
	 * @param defaultValue
	 * @return
	 * @author mkbyme Jan 27, 2019
	 */
	public static String getString(EnumConfigKey configKey, String defaultValue) {
		String optionValue = defaultValue;
		try {
			Object obj = Config.get(configKey);
			if (obj != null) {
				optionValue = obj.toString();
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ": Read not null:" + (++count));
				}
			} else {
				Config.put(configKey, optionValue, true);
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ": Read null + save:" + (++count));
				}
			}
		} catch (Exception e) {
			optionValue = defaultValue;
			e.printStackTrace();
			CommonLog.logError(e);
			Config.put(configKey, defaultValue, true);
			if (isDebug) {
				System.out.println(System.currentTimeMillis() + ": Read null + save + exception:" + (++count));
			}
		}

		return optionValue;
	}

	/**
	 * Get option setting return Int
	 * 
	 * @param configKey
	 * @param defaultValue
	 * @return
	 * @author mkbyme Jan 27, 2019
	 */
	public static int getInt(EnumConfigKey configKey, int defaultValue) {
		int optionValue = defaultValue;
		try {
			Object obj = Config.get(configKey);
			if (obj != null) {
				optionValue = Integer.parseInt(obj.toString());
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ": Read not null:" + (++count));
				}
			} else {
				if (isDebug) {
					System.out.println(System.currentTimeMillis() + ":Read null + save:" + (++count));
				}
				Config.put(configKey, defaultValue, true);
			}
		} catch (NumberFormatException e) {
			optionValue = defaultValue;
			e.printStackTrace();
			CommonLog.logError(e);
			Config.put(configKey, defaultValue, true);
			if (isDebug) {
				System.out.println(System.currentTimeMillis() + ": Read null + save + exception:" + (++count));
			}
		}

		return optionValue;
	}
}
