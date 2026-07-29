package resource.text;

import java.beans.Beans;
import java.util.MissingResourceException;
import java.util.ResourceBundle;

public class Messages {
	////////////////////////////////////////////////////////////////////////////
	//
	// Bundle access
	//
	////////////////////////////////////////////////////////////////////////////
	/// GLOBAL TEXT
	private static final String BUNDLE_GLOBAL_NAME = "resource.text.global"; //$NON-NLS-1$
	private static final ResourceBundle RESOURCE_GLOBAL_BUNDLE = loadGlobalBundle();
	/// UI TEXT
	private static final String BUNDLE_NAME = "resource.text.messages"; //$NON-NLS-1$
	private static final ResourceBundle RESOURCE_BUNDLE = loadBundle();

	////////////////////////////////////////////////////////////////////////////
	//
	// Strings access
	//
	////////////////////////////////////////////////////////////////////////////
	public static String getGlobalString(String key) {
		try {
			ResourceBundle bundle = Beans.isDesignTime() ? loadGlobalBundle() : RESOURCE_GLOBAL_BUNDLE;
			return bundle.getString(key);
		} catch (MissingResourceException e) {
			return "!" + key + "!";
		}
	}

	public static String getString(String key) {
		try {
			ResourceBundle bundle = Beans.isDesignTime() ? loadBundle() : RESOURCE_BUNDLE;
			return bundle.getString(key);
		} catch (MissingResourceException e) {
			return "!" + key + "!";
		}
	}

	private static ResourceBundle loadBundle() {
		return ResourceBundle.getBundle(BUNDLE_NAME);
	}

	private static ResourceBundle loadGlobalBundle() {
		return ResourceBundle.getBundle(BUNDLE_GLOBAL_NAME);
	}

	////////////////////////////////////////////////////////////////////////////
	//
	// Constructor
	//
	////////////////////////////////////////////////////////////////////////////
	private Messages() {
		// do not instantiate
	}
}
