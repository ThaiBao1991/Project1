package utils;

import java.beans.XMLDecoder;
import java.beans.XMLEncoder;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;

public class XMLParse {

	@SuppressWarnings("resource")
	public static Object loadConfig(String filePath)
			throws FileNotFoundException, NullPointerException, ClassNotFoundException, NoSuchMethodException {
		Object o = null;
		o = new XMLDecoder(new BufferedInputStream(new FileInputStream(filePath))).readObject();
		return o;
	}

	public static void saveConfig(String filePath, Object object) throws FileNotFoundException {

		XMLEncoder encoder;
		encoder = new XMLEncoder(new BufferedOutputStream(new FileOutputStream(filePath)));
		encoder.writeObject(object);
		encoder.close();

	}

}
