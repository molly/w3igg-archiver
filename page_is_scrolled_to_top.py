class page_is_scrolled_to_top(object):
    """An expectation for checking that a page has been scrolled all the way to the top."""

    def __call__(self, driver):
        scroll_top = driver.execute_script("return document.documentElement.scrollTop")
        return scroll_top == 0
