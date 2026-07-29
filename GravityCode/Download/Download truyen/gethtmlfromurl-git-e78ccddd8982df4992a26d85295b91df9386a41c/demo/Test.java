import org.jsoup.nodes.Document;

import utils.cloudflarebypass.CloudFlareByPass;

public class Test {

	public static void main(String[] args) {
		Document result = CloudFlareByPass
				.byPassCloudFlareGetDocument("https://truyencv.com/quang-minh-giao-dinh-tai-tu-chan-the-gioi/", 1);
		Document result2 = CloudFlareByPass
				.byPassCloudFlareGetDocument("https://truyencv.com/co-nguoi-quang-doi-con-lai-deu-ngot/", 1);
		Document result3 = CloudFlareByPass
				.byPassCloudFlareGetDocument("https://truyencv.com/co-nguoi-quang-doi-con-lai-deu-ngot/chuong-1/", 1);

		System.out.println("HTML1 => [" + result.selectFirst("h1,h2").html() + "]");
		System.out.println("HTML2 => [" + result2.selectFirst("h1,h2").html() + "]");
		System.out.println("HTML3 => [" + result3.selectFirst("h2").html() + "]");
	}

}
