(function () {
  const translations = {
    "Books": "Sách",
    "Blog": "Blog",
    "Create a Blog": "Tạo Blog",
    "Courses": "Khóa học",
    "Start Learning": "Bắt đầu học",
    "Register": "Đăng ký",
    "Support": "Ủng hộ",
    "Study time:": "Thời gian học:",
    "Pause": "Tạm dừng",
    "Resume": "Tiếp tục",
    "ARE YOU READY TO LEARN?": "BẠN ĐÃ SẴN SÀNG HỌC CHƯA?",
    "Learn With Fun": "Học thật vui",
    "on": "với",
    "any schedule": "lịch trình linh hoạt",
    "Now-a-days programming is one of the booming career in industry. It is profitable for one to learn programming as there is an enormous demand for good programmers in the industry.": "Ngày nay, lập trình là một trong những ngành nghề phát triển mạnh. Học lập trình mở ra nhiều cơ hội vì nhu cầu tuyển dụng lập trình viên giỏi luôn rất lớn.",
    "DONATE": "QUYÊN GÓP",
    "10+ Topic": "Hơn 10 chủ đề",
    "Technology For Everyone": "Công nghệ dành cho mọi người",
    "750+ Students": "Hơn 750 học viên",
    "Learn Programming": "Học lập trình",
    "9K+ Test Token": "Hơn 9K bài kiểm tra",
    "Learn Anythings": "Học mọi điều",
    "760+ Student": "Hơn 760 học viên",
    "Online Courses": "Khóa học trực tuyến",
    "Getting started with CPP": "Bắt đầu với C++",
    "Kickstart your journey in Java": "Bắt đầu hành trình Java",
    "Kickstart you coding journey with C": "Bắt đầu hành trình lập trình với C",
    "Getting started with Python": "Bắt đầu với Python",
    "Master Django Skills": "Thành thạo Django",
    "Learn HTML to create amazing web pages": "Học HTML để tạo nên những trang web ấn tượng",
    "Design Amazing Web Pages with CSS": "Thiết kế trang web tuyệt đẹp với CSS",
    "Kickstart you coding journey in Scripting": "Bắt đầu hành trình lập trình với ngôn ngữ kịch bản",
    "Learn Amazing Front-end Framework": "Khám phá framework giao diện tuyệt vời",
    "Kickstart you coding journey in Kotlin": "Bắt đầu hành trình lập trình với Kotlin",
    "Head for Google's Framework": "Khám phá framework của Google",
    "Start Understanding Databases": "Bắt đầu tìm hiểu cơ sở dữ liệu",
    "Kickstart you coding journey in Flutter": "Bắt đầu hành trình lập trình với Flutter",
    "Explore Machine Learning with PyTorch": "Khám phá học máy với PyTorch",
    "Create Dynamic Websites with PHP": "Tạo trang web động với PHP",
    "Create a REST API": "Tạo REST API",
    "Responsive Web Designs with Tailwind CSS": "Thiết kế web tương thích với Tailwind CSS",
    "Create Interactive Websites with Bootstrap": "Tạo trang web tương tác với Bootstrap",
    "Enroll": "Đăng ký học",
    "Available": "Còn chỗ",
    "Helping people to grow their careers, every day!": "Giúp mọi người phát triển sự nghiệp mỗi ngày!",
    "If you want to start your career in programming then this is for you, You can learn programming free of cost so stay tuned with us and if you have any query then register yourself.": "Nếu bạn muốn bắt đầu sự nghiệp lập trình, đây là nơi dành cho bạn. Hãy cùng chúng tôi học lập trình miễn phí; nếu có câu hỏi, hãy đăng ký để được hỗ trợ.",
    "Start": "Bắt đầu",
    "Any adept programmer, not only needs to be good at programming but also has to stay abreast of the upcoming happenings in programming. Just learning to code won't give you a big edge over the others.": "Một lập trình viên giỏi không chỉ cần viết code tốt mà còn phải cập nhật những xu hướng mới. Chỉ học lập trình thôi chưa đủ để tạo lợi thế vượt trội.",
    "Most good programmers do programming not because they expect to get paid or get adulation by the public, but it is fun to program.": "Nhiều lập trình viên giỏi viết chương trình không phải vì tiền bạc hay sự nổi tiếng, mà vì lập trình thực sự thú vị.",
    "Site owner": "Chủ trang web",
    "Do you want to be an instructor?": "Bạn muốn trở thành giảng viên?",
    "Join With Us": "Tham gia cùng chúng tôi",
    "About Us": "Về chúng tôi",
    "People of all ages and from around the world are improving their lives with us": "Mọi người ở mọi lứa tuổi trên khắp thế giới đang cải thiện cuộc sống cùng chúng tôi",
    "Courses Offered": "Các khóa học",
    "Machine Learning": "Học máy",
    "Web Design": "Thiết kế web",
    "Java Advance": "Java nâng cao",
    "Android Development": "Phát triển Android",
    "Connect With Us": "Kết nối với chúng tôi",
    "Additional Links": "Liên kết khác",
    "Contributors": "Người đóng góp",
    "Support Us": "Ủng hộ chúng tôi"
  };

  const textNodes = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!node.parentElement.closest("script, style")) {
      textNodes.push({ node: node, original: node.nodeValue });
    }
  }

  const languageSelect = document.getElementById("languageSelect");
  const storageKey = "e-learning-language";

  function detectLanguage() {
    try {
      const savedLanguage = localStorage.getItem(storageKey);
      if (savedLanguage === "en" || savedLanguage === "vi") {
        return savedLanguage;
      }
    } catch (error) {
      // Continue with browser-language detection when storage is unavailable.
    }

    return navigator.language && navigator.language.toLowerCase().startsWith("vi") ? "vi" : "en";
  }

  function setLanguage(language) {
    const useVietnamese = language === "vi";
    document.documentElement.lang = language;
    languageSelect.value = language;

    textNodes.forEach(function (entry) {
      const originalText = entry.original;
      const key = originalText.trim().replace(/\s+/g, " ");
      const translatedText = useVietnamese ? translations[key] : null;

      if (translatedText) {
        const leadingWhitespace = originalText.match(/^\s*/)[0];
        const trailingWhitespace = originalText.match(/\s*$/)[0];
        entry.node.nodeValue = leadingWhitespace + translatedText + trailingWhitespace;
      } else {
        entry.node.nodeValue = originalText;
      }
    });

    try {
      localStorage.setItem(storageKey, language);
    } catch (error) {
      // The current page still switches language if storage is unavailable.
    }

    document.dispatchEvent(new CustomEvent("site-language-change", { detail: { language: language } }));
  }

  languageSelect.addEventListener("change", function () {
    setLanguage(languageSelect.value);
  });

  setLanguage(detectLanguage());
})();