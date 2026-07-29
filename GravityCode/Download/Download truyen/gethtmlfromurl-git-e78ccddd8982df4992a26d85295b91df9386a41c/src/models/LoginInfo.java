package models;

import utils.UrlHandler;

/**
 * login info when get content form website
 * 
 * @author nxcuo
 * @since
 */
public class LoginInfo {
	String pageCode;
	String cookies;

	/**
	 * init to serilization
	 */
	public LoginInfo() {
	}

	/**
	 * init with pageCode
	 * 
	 * @param pageCode
	 */
	public LoginInfo(String pageCode) {
		this.pageCode = pageCode;
	}

	public String getPageCode() {
		return pageCode;
	}

	public void setPageCode(String pageCode) {
		this.pageCode = pageCode;
	}

	public String getCookies() {
		return cookies;
	}

	public void setCookies(String cookies) {
		this.cookies = cookies;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj) {
			return true;
		}
		if (obj == null) {
			return false;
		}
		if (getClass() != obj.getClass()) {
			return false;
		}
		LoginInfo other = (LoginInfo) obj;
		if (pageCode == null) {
			if (other.pageCode != null) {
				return false;
			}
		} else {
			// compare * host pattern interchanges
			if (pageCode.contains("*") || other.pageCode.contains("*")) {
				if (pageCode.contains("*") && !other.pageCode.contains(pageCode.replace("*", ""))) {
					return false;
				}
				if (other.pageCode.contains("*") && !pageCode.contains(other.pageCode.replace("*", ""))) {
					return false;
				}
			} else if (!UrlHandler.normalizeHost(pageCode).equals(UrlHandler.normalizeHost(other.pageCode))) {
				return false;
			}
		}
		return true;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((pageCode == null) ? 0 : pageCode.hashCode());
		return result;
	}
}
