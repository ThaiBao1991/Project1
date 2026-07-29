package utils;

import java.awt.HeadlessException;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

import javax.swing.JLabel;

import common.CommonExceptionHandle;
import common.CommonValue;
import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import common.Enumeration.UpdateState;
import log.CommonLog;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class CheckUpdate {
	public static void deleteOldVersion() {

		String lastVersionJarPath = SettingOption.getString(EnumConfigKey.DELETE_ON_EXIST, "");
		if (!lastVersionJarPath.isEmpty()) {
			try {
				Files.deleteIfExists(Paths.get(lastVersionJarPath));
				Config.remove(EnumConfigKey.DELETE_ON_EXIST);
				Config.saveConfig(Enumeration.ConfigType.Setting);

			} catch (Exception e) {
				try {

					Thread.sleep(1000);
					Files.deleteIfExists(Paths.get(lastVersionJarPath));
					Config.remove(EnumConfigKey.DELETE_ON_EXIST);
					Config.saveConfig(Enumeration.ConfigType.Setting);
				} catch (InterruptedException | IOException e2) {
					e2.printStackTrace();

				}
				e.printStackTrace();
				CommonLog.logError(e);
			}
		}

	}

	String fileToDownload = "";
	public String jarName = "";
	public String fileSize = "";
	public String message = "";
	public Date date = new Date();
	public Boolean isAppUpdated = false;
	public Boolean isConfigUpdated = false;
	/**
	 * update status reponse at start up checking
	 */
	public Enumeration.UpdateState updateStatus = UpdateState.NoNetWorking;

	/**
	 * check is has connect to the internet
	 * 
	 * @return true has connecting
	 */
	Boolean checkNetworking() {
		HttpURLConnection conn;
		try {
			conn = (HttpURLConnection) new URL("http://google.com").openConnection();
			;
			conn.setConnectTimeout(3000);
			conn.connect();
			conn.disconnect();
			return true;
		} catch (IOException e) {
			return false;
		}

	}

	void deleteOnStart() throws IOException {
		Config.put(common.Enumeration.EnumConfigKey.DELETE_ON_EXIST, CommonValue.getAppJARFile().getName());
		Config.saveConfig(Enumeration.ConfigType.Setting);

		java.awt.Desktop.getDesktop().open(new File(jarName));
		System.exit(0);
	}

	/**
	 * Check app is up to date
	 * 
	 * @return true updated
	 */
	public Enumeration.UpdateState isAppUpdate() {
		Enumeration.UpdateState updateState = UpdateState.GetAppUpdateInfoFailed;
		try {
			String updateString = GetFileUtil.getStringContentFromURI(
					CommonValue.getSourceForceDirectURL(Constant.SOURCEFORCE_UPDATE_FILE), 3000);
			if (updateString != "" && updateString.length() < 50) {
				updateState = UpdateState.AppOutOfUpdate;

				String updates[] = updateString.split(";");
				if (updates.length > 3) {

					updates[2] = updates[2].replace("\r\n", "");
					// setup value for download and show
					jarName = "GetTextFromHtml-V" + updates[0] + ".jar";
					fileSize = updates[2];
					try {
						date = new SimpleDateFormat("yyyy/MM/dd").parse(updates[1]);
					} catch (ParseException e) {
						CommonExceptionHandle.HandleException(e,
								Messages.getGlobalString("error.convertDatetimeError"));
					}
					fileToDownload = CommonValue.getSourceForceDirectURL(jarName);
					String[] newVersion = updates[0].split("\\.");
					String[] currentVersion = CommonValue.APP_VERSION.split("\\.");
					// compare Version
					int current, newVer;
					int tc = 0, tn = 0;
					for (int i = 0; i < currentVersion.length; i++) {
						current = Integer.parseInt(currentVersion[i]);
						newVer = Integer.parseInt(newVersion[i]);
						if (i == 0) {
							tc += current * 10000;
							tn += newVer * 10000;
						} else if (i == 1) {
							tc += current * 1000;
							tn += newVer * 1000;
						} else {
							if (newVer > 9 && current > 9) {
								tn += newVer;
								tc += current;
							} else if (newVer > 9) {
								tn += newVer;
								tc += current * 10;
							} else if (current > 9) {
								tn += newVer * 10;
								tc += current;
							} else {
								tn += newVer;
								tc += current;
							}
						}
					}
					if (tn > tc) {
						message = GetFileUtil.getStringContentFromURI(
								CommonValue.getSourceForceDirectURL(Constant.SOURCEFORCE_NEWS_FILE));
					} else {
						// app is updated
						updateState = UpdateState.AppUpdated;
					}
				} else {
					updateState = UpdateState.AppUpdated;
				}
			}

		} catch (Exception e) {
			e.printStackTrace();
			CommonLog.logError(e);
		}

		return updateState;
	}

	/**
	 * Check config is updated
	 * 
	 * @return true updated
	 */
	public Enumeration.UpdateState isConfigFileUpdate() {
		Enumeration.UpdateState updateStatus = UpdateState.ConfigOutOfUpdate;
		try {
			File currentConfigFile = new File(Constant.CONFIG_DATASITE_FILE);
			URL url = new URL(CommonValue.getDownloadLinkConfigFile());
			HttpURLConnection connection = (HttpURLConnection) url.openConnection();
			connection.setConnectTimeout(3000);
			long onlineLength = connection.getContentLengthLong();
			if (currentConfigFile.length() < onlineLength) {
				// setup value for download and show
				jarName = CommonValue.getAppJARFile().getName();
				fileToDownload = CommonValue.getDownloadLinkConfigFile();
				fileSize = (onlineLength / 1024) + " Kbs";
				message = GetFileUtil.getStringContentFromURI(
						CommonValue.getSourceForceDirectURL(Constant.SOURCEFORCE_NEWSHOST_FILE));
			} else {
				updateStatus = UpdateState.ConfigUpdated;
			}
		} catch (IOException e) {
			e.printStackTrace();
			CommonExceptionHandle.HandleException(e, Messages.getGlobalString("error.occurWhenCheckingUpdateConfig"));
		}
		return updateStatus;
	}

	/**
	 * Check update for application and config file.
	 * 
	 * @return true - all are update * @throws IOException
	 */
	public Boolean isUpdated() throws IOException {
		Boolean isUpdate = checkNetworking();
		// if not has network skip
		if (!isUpdate) {
			updateStatus = UpdateState.NoNetWorking;
		}

		// check app first
		updateStatus = isAppUpdate();
		switch (updateStatus) {
		case NoNetWorking:
		case GetAppUpdateInfoFailed:
			isAppUpdated = isConfigUpdated = true;
			break;
		case AppOutOfUpdate:
			isAppUpdated = isConfigUpdated = false;
			break;
		case AppUpdated:
			// if app is update to date -> check config
			isAppUpdated = true;
			updateStatus = isConfigFileUpdate();
			isConfigUpdated = isLastestConfig();
		default:
			break;
		}
		isUpdate = isAppUpdated && isConfigUpdated;
		return isUpdate;

	}

	public void setFileDownloadLink(String link) {
		fileToDownload = link;
	}

	/**
	 * perform action update app
	 * 
	 * @param lblStatus
	 *            - control to show update status
	 */
	public void updateApp(JLabel lblStatus) {
		Thread t = new Thread(new Runnable() {
			@Override
			public void run() {
				try {
					lblStatus.setText(Messages.getGlobalString("lblStatus.startingUpdate"));
					// jar file
					URL u = new URL(fileToDownload);

					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.dowloadingUpdate"), jarName, fileSize));
					ReadableByteChannel rbc = Channels.newChannel(u.openStream());
					FileOutputStream fos = new FileOutputStream(jarName);
					fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);

					fos.close();

					lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.downloadUpdateCompleted"),
							fileToDownload));

					// config file
					lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.downloadConfigFile"),
							Constant.CONFIG_DATASITE_FILE));
					u = new URL(CommonValue.getDownloadLinkConfigFile());
					rbc = Channels.newChannel(u.openStream());
					fos = new FileOutputStream(Constant.CONFIG_DATASITE_FILE);
					fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);

					fos.close();

					lblStatus.setText(Messages.getGlobalString("lblStatus.downloadConfigFileCompleted"));
					// complete
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 3));
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 2));
					Thread.sleep(1000);
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 1));
					Thread.sleep(1000);

					// delete current file at start and exit
					deleteOnStart();

				} catch (HeadlessException | IOException | InterruptedException e) {
					e.printStackTrace();
					CommonExceptionHandle.HandleException(e, Messages.getGlobalString("error.updateError"));
				}
			}
		});
		t.start();

	}

	/**
	 * perform action update config file
	 * 
	 * @param lblStatus
	 *            - control to show update status
	 * @throws IOException
	 */
	public void updateConfig(final JLabel lblStatus) throws IOException {
		Thread t = new Thread(new Runnable() {
			@Override
			public void run() {
				try {
					lblStatus.setText(Messages.getGlobalString("lblStatus.startingUpdate"));

					URL u = new URL(CommonValue.getDownloadLinkConfigFile());
					lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.downloadConfigFile"),
							Constant.CONFIG_DATASITE_FILE));
					ReadableByteChannel rbc = Channels.newChannel(u.openStream());
					FileOutputStream fos = new FileOutputStream(Constant.CONFIG_DATASITE_FILE);
					fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);
					fos.close();
					lblStatus.setText(Messages.getGlobalString("lblStatus.downloadConfigFileCompleted"));
					// complete
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 3));
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 2));
					Thread.sleep(1000);
					lblStatus.setText(
							String.format(Messages.getGlobalString("lblStatus.updateCompleteRestartAfterSecs"), 1));
					Thread.sleep(1000);
					// restart app
					java.awt.Desktop.getDesktop().open(CommonValue.getAppJARFile());

					System.exit(0);

				} catch (IOException | InterruptedException e) {
					e.printStackTrace();
					CommonLog.logError(e);
				}
			}
		});
		t.start();
	}

	/**
	 * check app is updated
	 */
	public Boolean isLastestVersion() {
		return this.updateStatus == UpdateState.AppUpdated;
	}

	/**
	 * check config is updated
	 */
	public Boolean isLastestConfig() {
		return this.updateStatus == UpdateState.ConfigUpdated;
	}

}
