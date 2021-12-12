import feedparser


class RSS_Fetch:

    def __init__(self, rss_url):
        self.rss_url = rss_url

        self.feed = feedparser.parse(self.rss_url)
        self.stories = self.feed.entries

    @property
    def num_stories(self):
        return len(self.stories)

    @property
    def story_keys(self):
        # Keys for stories are: ['title', 'title_detail', 'links', 'link', 'comments', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'wfw_commentrss', 'slash_comments', 'post-id']
        return self.stories[0].keys()

    @property
    def story_links(self):
        return [story['link'] for story in self.stories]
