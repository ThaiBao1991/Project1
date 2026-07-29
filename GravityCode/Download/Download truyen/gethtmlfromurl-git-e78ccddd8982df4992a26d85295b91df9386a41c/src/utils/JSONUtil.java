/**
 * 
 */
package utils;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;

import com.google.gson.Gson;
import com.google.gson.JsonIOException;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import common.CommonExceptionHandle;
import models.PageConfig;

/**
 * @author nxcuo process save and reading JSON data
 */
public class JSONUtil {
	/**
	 * list host config data type
	 */
	private final static Type CONFIG_DATASITE_TYPE = new TypeToken<ArrayList<PageConfig>>() {
	}.getType();

	public static ArrayList<PageConfig> loadConfig(String filePath)
			throws FileNotFoundException, JsonIOException, JsonSyntaxException {
		ArrayList<PageConfig> lstData = new ArrayList<>();
		Gson gson = new Gson();
		String jsonString = "";
		try {
			jsonString = new String(Files.readAllBytes(Paths.get(filePath)), StandardCharsets.UTF_8);

		} catch (IOException e) {
			e.printStackTrace();
		}

		lstData = gson.fromJson(jsonString, CONFIG_DATASITE_TYPE);

		return lstData;
	}

	public static void saveConfig(String filePath, Object object) throws FileNotFoundException {
		Gson gson = new Gson();
		OutputStreamWriter outWriter = null;

		try {
			outWriter = new OutputStreamWriter(new FileOutputStream(filePath), "UTF-8");
			String jsonString = gson.toJson(object);
			outWriter.write(jsonString);
		} catch (IOException e) {
			CommonExceptionHandle.HandleException(e, "Save config error");
			e.printStackTrace();
		} finally {
			if (outWriter != null) {
				try {
					outWriter.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}

	}
}
