# Insert method in class MetadataList results in an extra None Value in metadata list

Insert method of MetadataList Class inserts an extra None value in metadatalists, when e == i. Results in inequal length of metadata and list. When the insert occurs at the end of the iterable, no extra `None` is inserted. 

Bug found while writing 1,000 test cases for a Masters course I'm undertaking, let me know if you want all the tests. :) 

### Steps to Reproduce (for bugs)
1. Use the insert method of class MetadataList with a non-zero length MetadataList and insert the item not with the length of the iterable.


### Expected Behavior
- Only add the metadata that is being inserted and both lists (Metadata and __list being the same length).


### Current Behavior

- File location is in the root of the project, name doesn't matter for testing purposes.

#### Initialision

This section is setting up testing.

```python
from xl.common import MetadataList

def mock_metadata(title, **kwargs):
    return {"title": title } | kwargs

class MockSong:
    def __init__(self, title, **kwargs) -> None:
        self.__dict__ = mock_metadata(title,  **kwargs)

    @property
    def metadata(self):
        return self.__dict__
        
    def __eq__(self, other):
        if isinstance(other, MockSong):
            return self.metadata == other.metadata
        else:
            return NotImplemented
    
    def __str__(self) -> str:
        return f'{self.title} by {self.artist}'
    
    def __repr__(self) -> str:
        return f'MockSong("{self.title}")'

def mock_songs_with_metadata(num_songs=10):
	song_list = [MockSong(f"Song {x}") for x in range(num_songs)]
	meta_list = [x.metadata for x in song_list]
	return (song_list, meta_list)

def mock_song():
    return MockSong("Insert Song")

NUM_OF_SONGS = 5
song_list, meta_list = mock_songs_with_metadata(NUM_OF_SONGS)
mdl = MetadataList(song_list, meta_list)

def reset_mdl():
    song_list, meta_list = mock_songs_with_metadata(NUM_OF_SONGS)
    global mdl
    mdl = MetadataList(song_list, meta_list)  
```

#### Insert at Beggining

When the index is 0, the None Value is at index 1. The inserted object and metadata is in the correct location but the metadata after index 0 is 1 position out.

```python
metadata = [
	{'title': 'Insert Song'}, 
	None, 
	{'title': 'Song 0'}, 
	{'title': 'Song 1'}, 
	{'title': 'Song 2'}, 
	{'title': 'Song 3'}, 
	{'title': 'Song 4'}
]
```

For reference:

```python
class MetadataList:
	def __setitem__(self, i, value):
        self.__list.__setitem__(i, value)
        if isinstance(value, MetadataList):
            metadata = list(value.metadata)
        else:
            metadata = [None] * len(value)
        self.metadata.__setitem__(i, metadata)

	def insert(self, i, item, metadata=None):
        if i >= len(self):
            i = len(self)
            e = len(self) + 1
        else:
            e = i
        self[i:e] = [item]
        self.metadata[i:e] = [metadata]
```

##### Explanation

The bug is in `self.metadata[i:e] = [metadata]`. 

1. When the index `i` is less than the length, i.e. being inserted, the else clause is used; both e and i are equal `e = i`.
1. The line `self[i:e] = [item]` goes directly into the __setitem__ method and the value is of type list.
1. This means that `metadata = [None] * len(value)` line will get hit generating a `[None]` value.
1. As the index is a slice object of two equal integers, it will insert list into this list similar to adding two lists but will insert at the given location; the `None` value is inserted; `self.metadata.__setitem__(i, metadata)` sets the `None` value in the Metadata.

	```python
	self.metadata = [
		None, 
		{'title': 'Song 0'}, 
		{'title': 'Song 1'}, 
		{'title': 'Song 2'}, 
		{'title': 'Song 3'}, 
		{'title': 'Song 4'}
	]
	```

1. Return to the `insert` method.
1. Again a slice is used to insert the actual metadata value, resulting in:

	```python
	metadata = [
		{'title': 'Insert Song'}, 
		None, 
		{'title': 'Song 0'}, 
		{'title': 'Song 1'}, 
		{'title': 'Song 2'}, 
		{'title': 'Song 3'}, 
		{'title': 'Song 4'}
	]
	```


##### Example Code for Beggining

```python
reset_mdl()
insert_song = mock_song()
mdl.insert(0, insert_song, insert_song.metadata)
print(f"{len(mdl)} != {len(mdl.metadata)}")
print(mdl)
print(mdl.metadata)
```

#### Insert in the Middle

When the index is 2, the None Value is at index 3. The inserted object is in the correct location but the metadata is 1 position out after 2. Caused by the same bug as above.

```python
metadata = [
	{'title': 'Song 0'}, 
	{'title': 'Song 1'},
	{'title': 'Insert Song'}, 
	None, 
	{'title': 'Song 2'}, 
	{'title': 'Song 3'}, 
	{'title': 'Song 4'}
]
```

##### Example Code for Middle

```python
reset_mdl()
insert_song = mock_song()
mdl.insert(2, insert_song, insert_song.metadata)
print(f"{len(mdl)} != {len(mdl.metadata)}")
print(mdl)
print(mdl.metadata)
```

#### Insert at the End

When the object is inserted at the end i.e. appended, the list is correct.

```python
[
	{'title': 'Song 0'}, 
	{'title': 'Song 1'},
	{'title': 'Song 2'}, 
	{'title': 'Song 3'}, 
	{'title': 'Song 4'},
	{'title': 'Insert Song'}
]
```

```python
reset_mdl()
insert_song = mock_song()
mdl.insert(5, insert_song, insert_song.metadata)
print(f"{len(mdl)} == {len(mdl.metadata)}")
print(mdl)
print(mdl.metadata)
```

### Possible Solution

As the metadata list has been increased in size by the `MetadataList.__setitem__` with the value of None. It is safe to just use the index value `i`. 

```python
class MetadataList:
    def insert(self, i, item, metadata=None):
        if i >= len(self):
            i = len(self)
            e = len(self) + 1
        else:
            e = i
        self[i:e] = [item]
        self.metadata[i:e] = [metadata]
```

Proposed change:

```python
class MetadataList:
    def insert(self, i, item, metadata=None):
        if i >= len(self):
            i = len(self)
            e = len(self) + 1
        else:
            e = i
        self[i:e] = [item] 
        self.metadata[i] = metadata
```

1. After `self[i:e] = [item]` the metadata has a `None` value.
1. Change the 'None" value to the correct value with `self.metadata[i] = metadata`

### Environment
<!--- Include as many relevant details about the environment you experienced the bug in -->
* Operating System and version: Ubuntu 22.04 - Python 3.10
<!-- paste below all the version/locale information from the Exaile About dialog -->
* Exaile Version: 4.1.3 (76accdc14cf35ddb4e71c9b8722cdabd6d7c8e9e)

