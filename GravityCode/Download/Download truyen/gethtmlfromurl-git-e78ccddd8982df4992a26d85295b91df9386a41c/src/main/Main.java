package main;

import java.awt.EventQueue;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.awt.Rectangle;
import java.io.File;
import java.io.IOException;
import java.util.TimerTask;

import common.CommonValue;
import javafx.application.Platform;
import log.CommonLog;
import main.tweak.QuickLoginFromCookies;
import mk.constant.Constant;
import mkbrowser.MKBrowser;
import mkgethtml.Config;
import resource.text.Messages;
import utils.CheckUpdate;

public class Main {
	public static UI window;
	public static PageConfigManager pageConfigManager;
	public static Setting setting;
	public static MKBrowser browser;
	public static ManualGetUI manualGetUI;
	public static QuickLoginFromCookies quickLogin;

	public static void main(String args[]) throws Exception {

		Config.initConfig();

		Platform.setImplicitExit(false);
		// change cert
		File f = new File("jssecacerts");
		if (f.exists()) {
			System.setProperty("javax.net.ssl.trustStore", "jssecacerts");
		}

		System.setProperty("file.encoding", Constant.DEFAULT_ENCODING);
		if (args.length == 0) {
			EventQueue.invokeLater(new Runnable() {
				@Override
				public void run() {
					try {
						// splash screen
						java.util.Timer timer = new java.util.Timer("Loading");
						timer.schedule(new TimerTask() {
							@Override
							public void run() {
								try {
									window = new UI();

									SplashScreen ss = new SplashScreen();
									ss.pack();
									GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
									GraphicsDevice defaultScreen = ge.getDefaultScreenDevice();
									Rectangle rect = defaultScreen.getDefaultConfiguration().getBounds();
									int x =(int) rect.getMaxX() - ss.getWidth() - 70;
									int y = (int) rect.getMaxY() - ss.getHeight() - 70;
									ss.setLocation(x, y);
									ss.setVisible(true);
									ss.setStatus(Messages.getGlobalString("lblStatus.checkingUpdate"));

									window.jfrmUiGetHtml.setVisible(true);

									// check and not show frameUpdate
									CheckUpdate c = window.checkUpdate(true);
									Update frameUpdate = null;
									// if has update show update dialog
									if (!c.isAppUpdated || !c.isConfigUpdated) {
										if (!c.isAppUpdated) {

											ss.setStatus(String.format(Messages.getGlobalString("notify.hasNewVersion"),
													c.jarName.replaceAll("[^\\.\\d]", "")));
											Thread.sleep(1000);
											ss.setVisible(false);

											frameUpdate = new Update(
													String.format(Messages.getGlobalString("notify.updateSoftware"),
															CommonValue.APP_VERSION,
															c.jarName.replaceAll("[^\\.\\d]", "")),
													c.message, Messages.getGlobalString("btn.update"),
													Messages.getGlobalString("btn.skip"), c);

										} else if (!c.isConfigUpdated) {
											ss.setStatus(String.format(
													Messages.getGlobalString("lblStatus.hasNewConfigUpdate"),
													c.message.substring(0, 20)));
											Thread.sleep(1000);
											ss.setVisible(false);

											frameUpdate = new Update(
													Messages.getGlobalString("notify.updateNweConfigFile"), c.message,
													Messages.getGlobalString("btn.update"),
													Messages.getGlobalString("btn.skip"), c);

										}
										frameUpdate.frmUpdate.setVisible(true);
									} // else show UI frame
									else {
										Thread.sleep(100);
										// case to show result of update failed
										String messageUpdateStatus = "";
										switch (c.updateStatus) {
										case NoNetWorking:
											messageUpdateStatus = Messages.getGlobalString("lblStatus.noNetworking");
											break;
										case GetAppUpdateInfoFailed:
											messageUpdateStatus = Messages
													.getGlobalString("lblStatus.getUpdateInfoFailed");
											break;

										default:
											messageUpdateStatus = Messages.getGlobalString("lblStatus.allAreUpdate");
											break;
										}

										ss.setStatus(messageUpdateStatus);
										Thread.sleep(250);
										ss.setVisible(false);
										Thread.sleep(100);

										window.jfrmUiGetHtml.setVisible(true);
									}

								} catch (IOException | InterruptedException e) {
									e.printStackTrace();
								}
							}
						}, 100);

					} catch (Exception e) {
						e.printStackTrace();
					}
				}
			});
		} else {
			// turn off laucher
			if (args[0].toLowerCase().equals("launcher")) {
				if (args[1].toLowerCase().equals("off")) {
					window = new UI();
					window.jfrmUiGetHtml.setVisible(true);

				}
			}
		}
		// delete on exist of CheckUpdate;
		CheckUpdate.deleteOldVersion();
	}

	/**
	 * update all combo host on all UI if display
	 */
	public static void updateHostList() {
		try {
			if (Main.window != null) {
				Main.window.getListToCombo("");
			}
			if (Main.manualGetUI != null) {
				Main.manualGetUI.getListToCombo("");
			}
		} catch (Exception e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}
	}
}
