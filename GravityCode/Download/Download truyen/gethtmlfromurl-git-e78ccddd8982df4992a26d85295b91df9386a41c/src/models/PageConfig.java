package models;

import common.Enumeration;
import resource.text.Messages;
import utils.UrlHandler;

public class PageConfig {

	private String pageCode;
	private String pagingPattern;
	private String cssQueryGetListChapter;
	private String cssQueryGetChapterTitle;
	private String cssQueryGetChapterContent;
	private String urlPageTest;
	private String textGuide;
	private String cssFilter;
	private Boolean isManualGet;
	private Boolean isChapterLinkAsolute;
	private Boolean isEnableChapterSign;
	private Boolean isRevertChapterList = false;
	private Boolean isForumType = false;
	private Enumeration.OverMaxSizePageCountState overMaxSizePageCountState;
	private Boolean isUseJsoupGet = true;
	private Boolean isVietNameseHost = false;
	private String scriptJS = "";
	private Boolean byPassCloudFlare = false;
	private String mainHost;
	private Boolean useBruteForceMethod = false;

	public PageConfig() {
		isManualGet = false;
		isChapterLinkAsolute = true;
		isEnableChapterSign = false;
	}

	public PageConfig(String pageCode) {
		this.pageCode = pageCode;
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
		PageConfig other = (PageConfig) obj;
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

	public String getCssFilter() {
		return cssFilter;
	}

	public String getCssQueryGetChapterContent() {
		return cssQueryGetChapterContent;
	}

	public String getCssQueryGetChapterTitle() {
		return cssQueryGetChapterTitle;
	}

	public String getCssQueryGetListChapter() {
		return cssQueryGetListChapter;
	}

	public Boolean getIsChapterLinkAsolute() {
		return isChapterLinkAsolute;
	}

	public Boolean getIsEnableChapterSign() {
		return isEnableChapterSign;
	}

	public Boolean getIsForumType() {
		return isForumType;
	}

	public Boolean getIsManualGet() {
		return isManualGet;
	}

	public Boolean getIsRevertChapterList() {
		return isRevertChapterList;
	}

	public Enumeration.OverMaxSizePageCountState getOverMaxSizePageCountState() {
		return overMaxSizePageCountState;
	}

	public String getPageCode() {
		return pageCode;
	}

	public String getPagingPattern() {
		return pagingPattern;
	}

	public String getTextGuide() {
		return textGuide;
	}

	public String getUrlPageTest() {
		return urlPageTest;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((pageCode == null) ? 0 : pageCode.hashCode());
		return result;
	}

	public void setCssFilter(String cssRemoveContent) {
		this.cssFilter = cssRemoveContent;
	}

	public void setCssQueryGetChapterContent(String cssQueryGetChapterContent) {
		this.cssQueryGetChapterContent = cssQueryGetChapterContent;
	}

	public void setCssQueryGetChapterTitle(String cssQueryGetChapterTitle) {
		this.cssQueryGetChapterTitle = cssQueryGetChapterTitle;
	}

	public void setCssQueryGetListChapter(String cssQueryGetListChapterContaint) {
		this.cssQueryGetListChapter = cssQueryGetListChapterContaint;
	}

	public void setIsChapterLinkAsolute(Boolean isChapterLinkAsolute) {
		this.isChapterLinkAsolute = isChapterLinkAsolute;
	}

	public void setIsEnableChapterSign(Boolean isEnableChapterSign) {
		this.isEnableChapterSign = isEnableChapterSign;
	}

	public void setIsForumType(Boolean isForumType) {
		this.isForumType = isForumType;
	}

	public void setIsManualGet(Boolean isManualGet) {
		this.isManualGet = isManualGet;
	}

	public void setIsRevertChapterList(Boolean isRevertChapterList) {
		this.isRevertChapterList = isRevertChapterList;
	}

	public void setOverMaxSizePageCountState(Enumeration.OverMaxSizePageCountState overMaxSizePageCountState) {
		this.overMaxSizePageCountState = overMaxSizePageCountState;
	}

	public void setPageCode(String pageCode) {
		this.pageCode = pageCode;
	}

	public void setPagingPattern(String pagingPattern) {
		this.pagingPattern = pagingPattern;
	}

	public void setTextGuide(String textGuide) {
		this.textGuide = textGuide;
	}

	public void setUrlPageTest(String urlPageTest) {
		this.urlPageTest = urlPageTest;
	}

	@Override
	public String toString() {
		String location = (isVietNameseHost == true ? Messages.getGlobalString("const.locationVietNam")
				: Messages.getGlobalString("const.locationInternational"));
		String hostType = (isForumType ? Messages.getGlobalString("const.hostType.forum")
				: Messages.getGlobalString("const.hostType.web"));
		String type = (isManualGet ? " - Manual" : "");
		return this.pageCode + type + " - " + hostType + ": " + location;
	}

	/**
	 * @return the isUseJsoupGet
	 */
	public Boolean getIsUseJsoupGet() {
		return isUseJsoupGet;
	}

	/**
	 * @param isUseJsoupGet
	 *            the isUseJsoupGet to set
	 */
	public void setIsUseJsoupGet(Boolean isUseJsoupGet) {
		this.isUseJsoupGet = isUseJsoupGet;
	}

	/**
	 * @return the isVietNameseHost
	 */
	public Boolean getIsVietNameseHost() {
		return isVietNameseHost;
	}

	/**
	 * @param isVietNameseHost
	 *            the isVietNameseHost to set
	 */
	public void setIsVietNameseHost(Boolean isVietNameseHost) {
		this.isVietNameseHost = isVietNameseHost;
	}

	/**
	 * @return the scriptJS
	 */
	public String getScriptJS() {
		return scriptJS;
	}

	/**
	 * @param scriptJS
	 *            the scriptJS to set
	 */
	public void setScriptJS(String scriptJS) {
		this.scriptJS = scriptJS;
	}

	public Boolean getByPassCloudFlare() {
		return byPassCloudFlare;
	}

	public void setByPassCloudFlare(Boolean byPassCloudFlare) {
		this.byPassCloudFlare = byPassCloudFlare;
	}

	public String getMainHost() {
		return mainHost;
	}

	public void setMainHost(String mainHost) {
		this.mainHost = mainHost;
	}

	public Boolean getUseBruteForceMethod() {
		return useBruteForceMethod;
	}

	public void setUseBruteForceMethod(Boolean useBruteForceMethod) {
		this.useBruteForceMethod = useBruteForceMethod;
	}

}
