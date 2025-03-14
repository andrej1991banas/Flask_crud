import unittest
from app import app, db, Item
from flask import url_for

class TestCRUDApp(unittest.TestCase):
    def setUp(self):
        """Set up a test client and in-memory database before each test."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SERVER_NAME'] = 'localhost'  # Required for url_for in tests
        app.config['APPLICATION_ROOT'] = '/'  # Optional
        app.config['PREFERRED_URL_SCHEME'] = 'http'  # Optional
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def add_test_item(self):
        """Helper method to add a test item to the database."""
        with app.app_context():
            item = Item(name="Test Item", description="Test Description")
            db.session.add(item)
            db.session.commit()
            return item.id  # Return the ID instead of the instance to avoid detachment

    def test_index_route(self):
        """Test the index route loads and returns a 200 status code."""
        with app.app_context():
            response = self.app.get(url_for('index'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Items List', response.data)

    def test_add_item(self):
        """Test adding a new item."""
        with app.app_context():
            # Test GET request to load the add form
            response = self.app.get(url_for('add_item'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Add New Item', response.data)

            # Test POST request to add an item
            response = self.app.post(url_for('add_item'), data={
                'name': 'New Item',
                'description': 'New Description'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'New Item', response.data)
            self.assertIn(b'Item added successfully!', response.data)

            # Verify in database
            item = Item.query.filter_by(name='New Item').first()
            self.assertIsNotNone(item)
            self.assertEqual(item.description, 'New Description')

    def test_edit_item(self):
        """Test editing an existing item."""
        with app.app_context():
            # Add a test item
            item_id = self.add_test_item()
            item = db.session.get(Item, item_id)  # Fetch fresh instance using recommended method

            # Test GET request to load the edit form
            response = self.app.get(url_for('edit_item', id=item.id))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Edit Item', response.data)

            # Test POST request to edit the item
            response = self.app.post(url_for('edit_item', id=item.id), data={
                'name': 'Updated Item',
                'description': 'Updated Description'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Updated Item', response.data)
            self.assertIn(b'Item updated successfully!', response.data)

            # Verify update in database
            updated_item = db.session.get(Item, item.id)
            self.assertEqual(updated_item.name, 'Updated Item')
            self.assertEqual(updated_item.description, 'Updated Description')

    def test_delete_item(self):
        """Test deleting an existing item."""
        with app.app_context():
            # Add a test item
            item_id = self.add_test_item()
            item = db.session.get(Item, item_id)  # Fetch fresh instance using recommended method

            # Test GET request to load the delete confirmation
            response = self.app.get(url_for('delete_item', id=item.id))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Delete Item', response.data)

            # Test POST request to delete the item
            response = self.app.post(url_for('delete_item', id=item.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Item deleted successfully!', response.data)

            # Verify deletion
            deleted_item = db.session.get(Item, item.id)
            self.assertIsNone(deleted_item)

    def test_pagination(self):
        """Test pagination functionality."""
        with app.app_context():
            # Add multiple items to test pagination
            for i in range(6):  # Add 6 items
                item = Item(name=f"Item {i}", description=f"Desc {i}")
                db.session.add(item)
            db.session.commit()

            # Test page 1
            response = self.app.get(url_for('index', page=1))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Item 0', response.data)
            self.assertIn(b'Item 4', response.data)
            self.assertNotIn(b'Item 5', response.data)

            # Test page 2
            response = self.app.get(url_for('index', page=2))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Item 5', response.data)
            # self.assertNotIn('Next »'.encode('utf-8'), response.data)  # No next page after page 2

if __name__ == '__main__':
    unittest.main()