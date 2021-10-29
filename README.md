# fictionDown
Small tool to down fictions and combine each chapter together.

# Requirements
```
queue
threading
requests
fake_useragent
lxml
```

# Usage
```
python index.py [url] [thread_num]
# [url]: The url which refers to the detail page of fiction.
# [thread_num] : The number of threads you want to create to down the fiction at once. (10 is the default, while 1 is recommended, since the website has a stirct limit of page loads.)
```