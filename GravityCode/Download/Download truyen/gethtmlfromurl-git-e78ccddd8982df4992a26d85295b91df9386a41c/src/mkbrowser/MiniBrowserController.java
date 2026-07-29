/**
 * 
 */
package mkbrowser;

import static javafx.concurrent.Worker.State.FAILED;

import java.io.IOException;
import java.lang.reflect.Field;
import java.net.CookieHandler;
import java.net.Proxy;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLStreamHandler;
import java.net.URLStreamHandlerFactory;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;

import javax.swing.SwingUtilities;

import common.Enumeration.EnumConfigKey;
import javafx.application.Platform;
import javafx.beans.value.ChangeListener;
import javafx.beans.value.ObservableValue;
import javafx.event.ActionEvent;
import javafx.event.EventHandler;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Alert;
import javafx.scene.control.Alert.AlertType;
import javafx.scene.control.Button;
import javafx.scene.control.ButtonBar.ButtonData;
import javafx.scene.control.ButtonType;
import javafx.scene.control.Label;
import javafx.scene.control.MenuButton;
import javafx.scene.control.MenuItem;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.TextField;
import javafx.scene.control.Tooltip;
import javafx.scene.image.Image;
import javafx.scene.input.KeyCode;
import javafx.scene.input.KeyEvent;
import javafx.scene.input.MouseEvent;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebEvent;
import javafx.scene.web.WebView;
import javafx.stage.Stage;
import javafx.util.Callback;
import log.CommonLog;
import main.Main;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import models.LoginInfo;
import resource.text.Messages;

/**
 * @author nxcuo
 *
 */
public class MiniBrowserController implements Initializable {

	public String homeAddres = "https://google.com.vn";
	public static String openUrl = "https://google.com.vn";
	private static final String BLANK_IMAGE_LOC = "https://upload.wikimedia.org/wikipedia/commons/c/ce/Transparent.gif";
	private static final String IMAGE_MIME_TYPE_PREFIX = "image/";
	private Boolean isLoadImage = true;
	public static int MaxHistoryBackForward = 50;
	public String pageCode = "";
	/*
	 * list address in history
	 */
	ArrayList<String> ListAddress = new ArrayList<>();
	/*
	 * cursor focus on history address
	 */
	private int currentAddressIndex = -1;
	/*
	 * is add new address to history
	 */
	private Boolean isAddNewAddress = true;
	@FXML
	Button btnBackward;
	@FXML
	Button btnForward;
	@FXML
	Button btnRefresh;
	@FXML
	Button btnHome;
	@FXML
	Button btnGo;
	@FXML
	TextField txtAddress;
	@FXML
	WebView wvMain;
	@FXML
	MenuButton mnubFunction;
	@FXML
	MenuItem mnuSaveLoginInfo;
	@FXML
	MenuButton mnubSetting;
	@FXML
	MenuItem mnuEnableImage;

	@FXML
	Label lblStatus;
	@FXML
	ProgressBar progressBar;

	WebEngine engine;

	Boolean isInitSuccess = false;

	@Override
	public void initialize(URL location, ResourceBundle resources) {
		init();
	}

	/*
	 * init ui
	 */
	void init() {
		try {
			this.isLoadImage = SettingOption.getBoolean(EnumConfigKey.ISLOADIMAGE, true);
		} catch (Exception e) {
			CommonLog.logError(e);
		}

		localized();
		engine = wvMain.getEngine();
		engine.setJavaScriptEnabled(true);
		engine.setUserAgent(Constant.USER_AGENT);
		txtAddress.setOnKeyPressed(new EventHandler<KeyEvent>() {

			@Override
			public void handle(KeyEvent event) {

				if (event.getCode() == KeyCode.ENTER) {
					String url = txtAddress.getText();
					url = url.trim();
					if (url.contains(" ")) {
						url = "https://www.google.com.vn/search?q=" + txtAddress.getText().trim();
					}
					// add new address
					isAddNewAddress = true;
					loadAddress(url);
				}

			}

		});
		txtAddress.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {
				txtAddress.selectAll();

			}
		});
		btnBackward.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {
				currentAddressIndex--;
				if (currentAddressIndex > -1 && currentAddressIndex < ListAddress.size()) {
					isAddNewAddress = false;
					loadAddress(ListAddress.get(currentAddressIndex));
				}

			}
		});
		btnForward.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {

				currentAddressIndex++;
				if (currentAddressIndex > -1 && currentAddressIndex < ListAddress.size()) {
					isAddNewAddress = false;
					loadAddress(ListAddress.get(currentAddressIndex));
				}

			}
		});
		btnHome.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {
				isAddNewAddress = true;
				loadAddress(homeAddres);

			}
		});
		btnRefresh.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {
				String url = txtAddress.getText();
				if (url.trim() != "") {
					isAddNewAddress = false;
					loadAddress(url);
				} else {
					txtAddress.requestFocus();
				}

			}
		});
		btnGo.setOnMouseClicked(new EventHandler<MouseEvent>() {

			@Override
			public void handle(MouseEvent event) {
				String url = txtAddress.getText();
				if (url.trim() != "") {
					isAddNewAddress = true;
					loadAddress(url);
				} else {
					txtAddress.requestFocus();
				}

			}
		});

		mnuEnableImage.setOnAction(new EventHandler<ActionEvent>() {

			@Override
			public void handle(ActionEvent event) {
				isLoadImage = !isLoadImage;
				// reconfig
				handleLoadingImageOnBrowser();
				Config.put(EnumConfigKey.ISLOADIMAGE, isLoadImage, true);

				if (isLoadImage) {
					mnuEnableImage.setText(Messages.getString("MKBrowser.fx.mnuDisableImage"));
				} else {
					mnuEnableImage.setText(Messages.getString("MKBrowser.fx.mnuEnableImage"));
				}
				String url = txtAddress.getText();
				if (url.trim() != "") {
					isAddNewAddress = false;
					loadAddress(url);
				} else {
					txtAddress.requestFocus();
				}

			}
		});
		// save login info
		mnuSaveLoginInfo.setOnAction(new EventHandler<ActionEvent>() {

			@Override
			public void handle(ActionEvent event) {

				Alert alert = new Alert(AlertType.CONFIRMATION);
				alert.setTitle(Messages.getString("MKBrowser.dialog.confirmLoggedTitle"));
				alert.setContentText(
						String.format(Messages.getString("MKBrowser.dialog.confirmLoggedAndSave"), pageCode));
				alert.setHeaderText(null);
				alert.setResultConverter(new Callback<ButtonType, ButtonType>() {

					@Override
					public ButtonType call(ButtonType param) {
						if (param != null && param.getButtonData() == ButtonData.OK_DONE) {
							// save cookies
							CookieHandler cookies = CookieHandler.getDefault();
							Map<String, List<String>> headers = new LinkedHashMap<String, List<String>>();
							Map<String, List<String>> cookiesMap = new LinkedHashMap<String, List<String>>();
							try {
								String location = engine.getLocation();
								cookiesMap = cookies.get(new URI(location), headers);
								List<String> lstCookies = cookiesMap.get("Cookie");

								if (lstCookies.size() > 0) {
									LoginInfo loginInfo = new LoginInfo(pageCode);
									loginInfo.setCookies(lstCookies.get(0));
									// save cookies
									if (location.toLowerCase().contains(pageCode.toLowerCase())) {
										Config.updateLoginInfo(loginInfo, pageCode);
									}
								}

							} catch (IOException | URISyntaxException e) {
								CommonLog.logError(e);
								e.printStackTrace();
							}

						}
						return param;
					}
				});
				Stage stage = (Stage) alert.getDialogPane().getScene().getWindow();
				stage.getIcons().add(new Image(getClass().getResource("/resource/box-16.png").toString()));
				alert.showAndWait();

			}
		});
		webEnginEvent();
		// handle loading image
		handleLoadingImageOnBrowser();
		isInitSuccess = true;
	}

	/*
	 * localized text
	 */
	private void localized() {
		mnubFunction.setText(Messages.getString("MKBrowser.fx.mnubFunction"));
		mnuSaveLoginInfo.setText(Messages.getString("MKBrowser.fx.mnuSaveLoginInfo"));

		mnubSetting.setText(Messages.getString("MKBrowser.fx.mnubSetting"));
		if (isLoadImage) {
			mnuEnableImage.setText(Messages.getString("MKBrowser.fx.mnuDisableImage"));
		} else {
			mnuEnableImage.setText(Messages.getString("MKBrowser.fx.mnuEnableImage"));
		}

		btnBackward.setTooltip(new Tooltip(Messages.getString("MKBrowser.btnBackward.toolTipText")));
		btnForward.setTooltip(new Tooltip(Messages.getString("MKBrowser.btnForward.toolTipText")));
		btnGo.setTooltip(new Tooltip(Messages.getString("MKBrowser.btnGo.toolTipText")));
		btnHome.setTooltip(new Tooltip(Messages.getString("MKBrowser.btnHome.toolTipText")));
		btnRefresh.setTooltip(new Tooltip(Messages.getString("MKBrowser.btnRefresh.toolTipText")));

		txtAddress.promptTextProperty().setValue(Messages.getString("MKBrowser.txtAddress.promtText"));
	}

	/*
	 * webengine event
	 */
	void webEnginEvent() {

		engine.titleProperty().addListener(new ChangeListener<String>() {
			@Override
			public void changed(ObservableValue<? extends String> observable, String oldValue, final String newValue) {
				SwingUtilities.invokeLater(new Runnable() {
					@Override
					public void run() {
						Main.browser.setTitle(newValue);
					}
				});
			}
		});

		// web engine event
		engine.setOnStatusChanged(new EventHandler<WebEvent<String>>() {
			@Override
			public void handle(final WebEvent<String> event) {
				lblStatus.setText(event.getData());
			}
		});
		engine.getLoadWorker().workDoneProperty().addListener(new ChangeListener<Number>() {
			@Override
			public void changed(ObservableValue<? extends Number> observableValue, Number oldValue,
					final Number newValue) {
				progressBar.setProgress(newValue.intValue());
			}
		});
		engine.getLoadWorker().exceptionProperty().addListener(new ChangeListener<Throwable>() {

			@Override
			public void changed(ObservableValue<? extends Throwable> o, Throwable old, final Throwable value) {
				if (engine.getLoadWorker().getState() == FAILED) {
					lblStatus.setText("Network error...!");
				}
			}
		});
		// show new address
		engine.locationProperty().addListener(new ChangeListener<String>() {
			@Override
			public void changed(ObservableValue<? extends String> ov, String oldValue, final String newValue) {
				SwingUtilities.invokeLater(new Runnable() {
					@Override
					public void run() {
						txtAddress.setText(newValue);
					}
				});
			}
		});
	}

	/*
	 * load website by url
	 */
	public void loadAddress(String url) {
		url = url.trim();
		if (!url.startsWith("http://") && !url.startsWith("https://")) {
			url = "http://" + url;
		}

		txtAddress.setText(url);
		engine.setUserAgent(Constant.USER_AGENT);
		
		engine.load(url);

		if (isAddNewAddress) {
			currentAddressIndex = ListAddress.size();
			if (ListAddress.size() > MaxHistoryBackForward) {
				ListAddress.remove(0);
				currentAddressIndex--;
			}
			ListAddress.add(url);
			isAddNewAddress = false;

		}
		btnBackward.setDisable(true);
		btnForward.setDisable(true);

		// has backward address -> enbale
		if (currentAddressIndex > 0) {
			btnBackward.setDisable(false);
		}
		// has forward address -> enbale
		if (currentAddressIndex > -1 && currentAddressIndex < (ListAddress.size() - 1)) {
			btnForward.setDisable(false);
		}
		wvMain.requestFocus();
	}

	/*
	 * load url from swing wait to fx load complete then load url
	 */
	public void loadAddressOnFirst(final String url) {

		Thread t = new Thread(new Runnable() {

			@Override
			public void run() {
				while (!isInitSuccess) {
					try {
						Thread.sleep(1000);
					} catch (InterruptedException e) {

						e.printStackTrace();
					}
				}
				// invoke java fx ui
				Platform.runLater(new Runnable() {

					@Override
					public void run() {
						loadAddress(url);
					}
				});

			}
		});

		t.start();

	}

	/*
	 * enable/disable image
	 */
	void handleLoadingImageOnBrowser() {
		Platform.runLater(new Runnable() {

			@Override
			public void run() {
				URLStreamHandlerFactory factory = new URLStreamHandlerFactory() {
					@Override
					public URLStreamHandler createURLStreamHandler(String protocol) {
						if ("http".equals(protocol)) {
							return new sun.net.www.protocol.http.Handler() {
								@Override
								protected URLConnection openConnection(URL url, Proxy proxy) throws IOException {
									String[] fileParts = url.getFile().split("\\?");
									String contentType = URLConnection.guessContentTypeFromName(fileParts[0]);

									if (fileParts[0].endsWith(".svg")) {
										contentType = "image/svg";
									}
									if ((contentType != null && contentType.startsWith(IMAGE_MIME_TYPE_PREFIX))) {
										if (isLoadImage) {
											return super.openConnection(url, proxy);
										} else {
											return new URL(BLANK_IMAGE_LOC).openConnection();
										}
									} else {
										return super.openConnection(url, proxy);
									}
								}
							};
						}

						return null;
					}
				};
				try {
					URL.setURLStreamHandlerFactory(factory);
				} catch (final Error e) {
					// force set factory
					Field factoryField;
					try {
						factoryField = URL.class.getDeclaredField("factory");
						factoryField.setAccessible(true);
						factoryField.set(null, factory);
					} catch (NoSuchFieldException | SecurityException | IllegalArgumentException
							| IllegalAccessException e1) {
						e1.printStackTrace();
						CommonLog.logError(e1);
					}

				}
			}
		});
	}
}
