package utils;

import java.util.Random;

/**
 * class processing ip address
 * 
 * @author mkbyme
 */
public class IpHandler {
	/**
	 * gen a random number
	 */
	private static final Random m_Random = new Random();
	/**
	 * create a new random ip address
	 * @return {@link String} A random Ip address
	 */
	public static String getNewIPAddress() {
		String sIp = "";
		sIp = m_Random.nextInt(256) + "." + m_Random.nextInt(256) + "." + m_Random.nextInt(256) + "." + m_Random.nextInt(256);
		return sIp;
	}
}
