// TEST CONTEXT MENUS - Dán từng lệnh vào Console để test

// Test 1: Hiện menu Tab tại vị trí (100,100)
hideAllContextMenus(); 
showSmartMenu(document.getElementById('notes-tab-context-menu'), 100, 100);

// Test 2: Hiện menu Card tại vị trí (200,200)  
hideAllContextMenus(); 
showSmartMenu(document.getElementById('note-card-context-menu'), 200, 200);

// Test 3: Hiện menu Editor (bôi đen text) tại vị trí (300,200)
hideAllContextMenus(); 
showSmartMenu(document.getElementById('notes-context-menu'), 300, 200);

// Test 4: Hiện menu Profile-span tại vị trí (400,200)
hideAllContextMenus(); 
showSmartMenu(document.getElementById('profile-span-context-menu'), 400, 200);

// Test 5: Hiện menu Thumbnail tại vị trí (500,200)
hideAllContextMenus(); 
showSmartMenu(document.getElementById('tg-thumb-context-menu'), 500, 200);

// Nếu tất cả 5 lệnh trên thấy menu bật, là fix OK!
// Khi đó chuột phải trên UI cũng sẽ chạy bình thường.
