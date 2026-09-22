(() => {
  const updateLanguageLinks = () => {
    const pathMatch = window.location.pathname.match(
      /^\/(?:zh-cn|en)\/([^/]+)(\/.*)?$/
    );

    if (!pathMatch) {
      return;
    }

    document.querySelectorAll(".hm-language-switch").forEach((link) => {
      const targetLanguage = link.dataset.targetLanguage;
      if (!targetLanguage) {
        return;
      }

      const targetUrl = new URL(link.href);
      targetUrl.pathname = `/${targetLanguage}/${pathMatch[1]}${pathMatch[2] || "/"}`;
      targetUrl.search = window.location.search;
      targetUrl.hash = window.location.hash;
      link.href = targetUrl.toString();
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateLanguageLinks);
  } else {
    updateLanguageLinks();
  }
})();
