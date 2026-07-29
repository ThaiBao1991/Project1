package models;

public class Chapter {
	private String title;
	private String content;
	private Boolean isHasCapchaBlock = false;
	/**
	 * Get content failure
	 */
	public Boolean isGetFailed = false;

	public Chapter() {
		this.title = "";
		this.content = "";
	}

	public Chapter(String title, String content) {
		super();
		this.title = title;
		this.content = content;
	}

	public String getContent() {
		return content;
	}

	public String getTitle() {
		return title;
	}

	public void setContent(String content) {
		this.content = content;
	}

	public void setTitle(String title) {
		this.title = title;
	}

	/**
	 * flags to know that this site has google capcha or not
	 * 
	 * @return the isHasCapchaBlock - true if has google reCapcha
	 */
	public Boolean getIsHasCapchaBlock() {
		return isHasCapchaBlock;
	}

	/**
	 * set flags to know that this site has google capcha or not
	 * 
	 * @param isHasCapchaBlock
	 *            the isHasCapchaBlock to set
	 */
	public void setIsHasCapchaBlock(Boolean isHasCapchaBlock) {
		this.isHasCapchaBlock = isHasCapchaBlock;
	}
}
