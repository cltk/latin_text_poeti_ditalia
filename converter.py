import os, re
import json
import pdb
from django.utils.text import slugify
import collections

sourceLink = 'http://www.poetiditalia.it/public/'
source = 'Poeti d’Italia in lingua latina'
works = []

def jaggedListToDict(text):
	node = { str(i): t for i, t in enumerate(text) }
	node = collections.OrderedDict(sorted(node.items(), key=lambda k: int(k[0])))
	for child in node:
		if isinstance(node[child], list):
			if len(node[child]) == 1:
				node[child] = node[child][0]
			else:
				node[child] = jaggedListToDict(node[child])
	return node

def main():

	if not os.path.exists('cltk_json'):
		os.makedirs('cltk_json')

	# Build json docs from txt files
	for root, dirs, files in os.walk("."):
		path = root.split('/')
		print((len(path) - 1) * '---', os.path.basename(root))
		for fname in files:
			if fname.endswith('json') and 'cltk_json' not in path:
				with open(os.path.join(root, fname)) as f:
					data_str = f.read()

				try:
					data = json.loads(data_str)
				except json.decoder.JSONDecodeError:
					# fight with linebreaks and unescaped quotation marks
					print('json.decoder.JSONDecodeError parsing text, attempting method with replacing linebreaks')
					data_str_with_linebreaks = data_str
					data_str = data_str.replace('\r', '').replace('\n', '')
					data_str_with_linebreaks = data_str_with_linebreaks.replace('\r', '\\r').replace('\n', '\\n')

					# escape unescaped quotation marks
					raw_text = re.search(r'"text":\s?".*"', data_str)
					raw_text = data_str[raw_text.start():raw_text.end()]
					_raw_text = raw_text.replace(
							raw_text[8:-1],
							raw_text[8:-1].replace('"', '\\"')
						)
					data_str = data_str.replace(raw_text, _raw_text)

					try:
						data = json.loads(data_str)
					except Exception as e:
						print('Unable to parse file', os.path.join(root, fname), 'with Error:', e)

					# ensure text has linebreaks
					raw_text = re.findall(r'"text":\s?".*"', data_str_with_linebreaks)
					if len(raw_text):
						data['text'] = raw_text[0].replace('"text":', "")
					else:
						print('Did not retrieve text from the raw json data string')
						print('-- manually review', root, fname)

					data['text'] = data['text'].replace('\\"', '\"')

				try:
					work = {
						'originalTitle': data['title'].title(),
						'englishTitle': data['title'].title(),
						'author': data['author'].title(),
						'source': source,
						'sourceLink': sourceLink,
						'language': 'latin',
						'text': {},
					}
				except:
					pdb.set_trace()

				# split text into lines
				data['text'] = re.split(r'\\n|\n', data['text'])
				data['text'] = [node.strip() for node in data['text'] if len(node.strip())]

				# ensure no lines are only ints
				text = []
				for node in data['text']:
					try:
						int(node)
					except ValueError:
						text.append(node)

				work['text'] = jaggedListToDict(text)
				fname = slugify(work['source']) + '__' + slugify(work['englishTitle'][0:140]) + '__' + slugify(work['language']) + '.json'
				fname = fname.replace(" ", "")
				with open('cltk_json/' + fname, 'w') as f:
					json.dump(work, f)

if __name__ == '__main__':
	main()
