package utils.cloudflarebypass;

/**
 * Enum list result when bypass cloudflare
 * 
 * @author mkbyme, Feb 10, 2019
 */
public enum CloudFlareByPassReultErrorType {
	OK("OK", 1), EXCEPTION("Exception", 2);
	/**
	 * Name of Enum
	 */
	private String name;
	/**
	 * Enum in Int
	 */
	private int value;

	CloudFlareByPassReultErrorType(String name, int value) {
		this.name = name;
		this.value = value;
	}

	public int getInt() {
		return value;
	}

	public String getName() {
		return name;
	}

	/**
	 * Get Enum from int value
	 * 
	 * @param value
	 *            - int value
	 * @return {@link CloudFlareByPassReultErrorType}
	 * @author mkbyme, Feb 10, 2019
	 */
	public CloudFlareByPassReultErrorType getEnumFromInt(int value) {
		CloudFlareByPassReultErrorType ret = OK;
		switch (value) {
		case 1:
			ret = OK;
			break;
		case 2:
			ret = EXCEPTION;
			break;
		}
		return ret;
	}
}
