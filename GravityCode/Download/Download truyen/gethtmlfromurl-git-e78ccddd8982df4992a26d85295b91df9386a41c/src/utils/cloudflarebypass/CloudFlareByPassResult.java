package utils.cloudflarebypass;

/**
 * 
 * Result when by pass cloudflare, OK to next process
 * 
 * @author mkbyme, Feb 11, 2019
 *
 */
public class CloudFlareByPassResult {
	private String cookies;
	private String cookiesName = "cf_clearance";
	private CloudFlareByPassReultErrorType errorType;

	public String getCookies() {
		return cookies;
	}

	public void setCookies(String cookies) {
		this.cookies = cookies;
	}

	/**
	 * Set cookies name and value
	 * 
	 * @param key
	 * @param value
	 * @author mkbyme, Feb 11, 2019
	 */
	public void setCookiesWithName(String key, String value) {
		this.cookiesName = key;
		this.cookies = value;
	}

	/**
	 * Retunr cookies with name(key=value;)
	 * 
	 * @return cf_clearance=value;
	 * @author mkbyme, Feb 11, 2019
	 */
	public String getCookiesWithName() {
		return String.format(";%s=%s;", this.cookiesName, this.cookies);
	}

	public CloudFlareByPassReultErrorType getErrorType() {
		return errorType;
	}

	public void setErrorType(CloudFlareByPassReultErrorType errorType) {
		this.errorType = errorType;
	}

	public String getCookiesName() {
		return cookiesName;
	}

	public void setCookiesName(String cookiesName) {
		this.cookiesName = cookiesName;
	}

}
